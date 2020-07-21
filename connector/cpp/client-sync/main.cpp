//
// Copyright (c) 2016-2019 Vinnie Falco (vinnie dot falco at gmail dot com)
//
// Distributed under the Boost Software License, Version 1.0. (See accompanying
// file LICENSE_1_0.txt or copy at http://www.boost.org/LICENSE_1_0.txt)
//
// Official repository: https://github.com/boostorg/beast
//

//------------------------------------------------------------------------------
//
// Example: WebSocket client, synchronous
//
//------------------------------------------------------------------------------

#include <boost/beast/core.hpp>
#include <boost/beast/ssl.hpp>
#include <boost/beast/websocket.hpp>
#include <boost/beast/websocket/ssl.hpp>

#include <chrono>
#include <cmath>
#include <cstdlib>
#include <iomanip>
#include <iostream>
#include <iterator>
#include <string>

#include "helpers.hpp"
#include "nlohmann/json.hpp"
#include "ore.hpp"
#include "root_certificates.hpp"

// for convenience
using json = nlohmann::json;

namespace beast = boost::beast;          // from <boost/beast.hpp>
namespace http = beast::http;            // from <boost/beast/http.hpp>
namespace websocket = beast::websocket;  // from <boost/beast/websocket.hpp>
namespace net = boost::asio;             // from <boost/asio.hpp>
namespace ssl = boost::asio::ssl;        // from <boost/asio/ssl.hpp>
using tcp = boost::asio::ip::tcp;        // from <boost/asio/ip/tcp.hpp>

// Sends a WebSocket message and prints the response
int main(int argc, char** argv) {
  try {
    // Check command line arguments.
    if (argc != 4) {
      std::cerr << "Usage: websocket-client-sync <host> <port> <text>\n"
                << "Example:\n"
                << "    websocket-client-sync echo.websocket.org 80 \"Hello, "
                   "world!\"\n";
      return EXIT_FAILURE;
    }
    std::string host = argv[1];
    auto const port = argv[2];
    auto const text =
        "{\"type\": \"subscribe\", \"product_ids\": [\"BTC-USD\"], "
        "\"channels\": [\"level2\", \"matches\"]}";  // argv[3];
    // auto start = std::chrono::high_resolution_clock::now();
    uint64_t seconds_to_epoch = 0;
    uint64_t sec_to_ns = 1000000000;
    int price_digits = 2;
    int qty_digits = 8;

    // The io_context is required for all I/O
    net::io_context ioc;
    ssl::context ctx{ssl::context::tlsv12_client};
    load_root_certificates(ctx);
    ctx.set_verify_mode(ssl::verify_none);

    // These objects perform our I/O
    websocket::stream<beast::ssl_stream<beast::tcp_stream>> ws{ioc, ctx};
    tcp::resolver resolver(ioc);

    if (!SSL_set_tlsext_host_name(ws.next_layer().native_handle(),
                                  "ws-feed.prime.coinbase.com")) {
      boost::system::error_code ec{static_cast<int>(::ERR_get_error()),
                                   boost::asio::error::get_ssl_category()};
      throw boost::system::system_error{ec};
    }

    // Look up the domain name
    auto const results = resolver.resolve(host, port);

    // Make the connection on the IP address we get from a lookup
    auto ep = beast::get_lowest_layer(ws).connect(results);

    ws.next_layer().handshake(ssl::stream_base::client);

    // Update the host_ string. This will provide the value of the
    // Host HTTP header during the WebSocket handshake.
    // See https://tools.ietf.org/html/rfc7230#section-5.4
    host += ':' + std::to_string(ep.port());

    // Set a decorator to change the User-Agent of the handshake
    ws.set_option(
        websocket::stream_base::decorator([](websocket::request_type& req) {
          req.set(http::field::user_agent,
                  std::string(BOOST_BEAST_VERSION_STRING) +
                      " websocket-client-coro");
        }));

    // Perform the websocket handshake
    ws.handshake(host, "/");

    // Send the message
    ws.write(net::buffer(std::string(text)));

    // This buffer will hold the incoming message
    beast::flat_buffer buffer;

    // Read a message into our buffer
    for (int i = 0; i != 10000; ++i) {
      ws.read(buffer);

      uint64_t exos_time =
          std::chrono::duration_cast<std::chrono::nanoseconds>(
              std::chrono::high_resolution_clock::now().time_since_epoch())
              .count();
      uint64_t elapsedEpoch = exos_time / sec_to_ns;
      int64_t t_ns = exos_time % sec_to_ns;

      json j = json::parse(beast::buffers_to_string(buffer.data()));
      std::string type = j["type"];

      if (type == "snapshot") {
        std::cout << "snap shotn";
        // vendor_offset is 0
        // an l2 message for every bid/ask
        auto bids = j["bids"];
        auto asks = j["asks"];
        int bid_switch = bids.size();
        bids.insert(bids.end(), asks.begin(), asks.end());

        for (auto bids_iter = bids.begin(); bids_iter != bids.end();
             ++bids_iter) {
          int price_field = str_to_intfield((*bids_iter)[0], price_digits);
          int qty_field = str_to_intfield((*bids_iter)[1], qty_digits);

          auto idx = std::distance(bids.begin(), bids_iter);

          LevelSet ore_msg(1, t_ns, 0, 0, 0, 0, price_field, qty_field,
                           idx < bid_switch ? "buy" : "sell");
          std::array<LevelSet, 1> arr = {ore_msg};
          msgpack::sbuffer sbuf;
          msgpack::pack(sbuf, arr);

          msgpack::object_handle oh = msgpack::unpack(sbuf.data(), sbuf.size());
          msgpack::object deserialized = oh.get();
          std::cout << deserialized << std::endl;
        }
      } else if (j["type"] != "subscriptions") {
        std::cout << j["type"] << std::endl;
        std::string ts = j["time"];
        uint64_t vendor_time = EpochConverter(ts);
        int64_t vendor_offset = vendor_time - exos_time;

        if (elapsedEpoch > seconds_to_epoch) {
          seconds_to_epoch = elapsedEpoch;
          Time ore_msg(0, seconds_to_epoch);
          std::array<Time, 1> arr = {ore_msg};
          msgpack::sbuffer sbuf;
          msgpack::pack(sbuf, arr);

          msgpack::object_handle oh = msgpack::unpack(sbuf.data(), sbuf.size());
          msgpack::object deserialized = oh.get();
          std::cout << deserialized << std::endl;
        }

        if (type == "l2update") {
          int price_field = str_to_intfield(j["changes"][0][1], price_digits);
          int qty_field = str_to_intfield(j["changes"][0][2], qty_digits);
          LevelSet ore_msg(14, t_ns, vendor_offset, 0, 0, 0, price_field,
                           qty_field, j["changes"][0][0] == "buy");
          std::array<LevelSet, 1> arr = {ore_msg};
          msgpack::sbuffer sbuf;
          msgpack::pack(sbuf, arr);

          msgpack::object_handle oh = msgpack::unpack(sbuf.data(), sbuf.size());
          msgpack::object deserialized = oh.get();
          std::cout << deserialized << std::endl;
        }

        else if (type == "match") {
          auto price_field = str_to_intfield(j["price"], price_digits);
          auto qty_field = str_to_intfield(j["size"], qty_digits);
          Match ore_msg(11, t_ns, vendor_offset, 0, 0, 0, price_field,
                        qty_field, j["side"] == "buy" ? "b" : "s");
          std::array<Match, 1> arr = {ore_msg};
          msgpack::sbuffer sbuf;
          msgpack::pack(sbuf, arr);

          msgpack::object_handle oh = msgpack::unpack(sbuf.data(), sbuf.size());
          msgpack::object deserialized = oh.get();
          std::cout << deserialized << std::endl;
        }
      }

      // drain buffer
      std::cout << "draining\n";
      buffer.consume(buffer.size());
    }

    // auto stop = std::chrono::high_resolution_clock::now();
    // std::cout << "closing! after: "
    //           << std::to_string(
    // std::chrono::duration_cast<std::chrono::nanoseconds>(stop
    //                  -
    // start)
    //                      .count())
    //           << std::endl;

    // Close the WebSocket connection
    ws.close(websocket::close_code::normal);

    // If we get here then the connection is closed gracefully

    // The make_printable() function helps print a ConstBufferSequence
    std::cout << beast::make_printable(buffer.data()) << std::endl;
  } catch (std::exception const& e) {
    std::cerr << "Error: " << e.what() << std::endl;
    return EXIT_FAILURE;
  }
  return EXIT_SUCCESS;
}
