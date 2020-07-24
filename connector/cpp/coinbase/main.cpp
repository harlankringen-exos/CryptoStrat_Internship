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
// connect to coinbase and liten for l2 and match updates
// msgpack the around 4 different ORE messages
//
//------------------------------------------------------------------------------

#include <boost/beast/core.hpp>
#include <boost/beast/ssl.hpp>
#include <boost/beast/websocket.hpp>
#include <boost/beast/websocket/ssl.hpp>

#include <chrono>
#include <cmath>
#include <csignal>
#include <cstdlib>
#include <fstream>
#include <iomanip>
#include <iostream>
#include <iterator>
#include <string>

#include "helpers.hpp"
//#include "nlohmann/json.hpp"
#include "ore.hpp"
#include "root_certificates.hpp"
//#include "simdjson.h"

// // for convenience
// using json = nlohmann::json;
// using namespace simdjson;  // optional
#include "rapidjson/document.h"
#include "rapidjson/pointer.h"
#include "rapidjson/stringbuffer.h"
#include "rapidjson/writer.h"

namespace beast = boost::beast;          // from <boost/beast.hpp>
namespace http = beast::http;            // from <boost/beast/http.hpp>
namespace websocket = beast::websocket;  // from <boost/beast/websocket.hpp>
namespace net = boost::asio;             // from <boost/asio.hpp>
namespace ssl = boost::asio::ssl;        // from <boost/asio/ssl.hpp>
using tcp = boost::asio::ip::tcp;        // from <boost/asio/ip/tcp.hpp>

struct timing_data {
  std::chrono::high_resolution_clock::time_point start;
  uint64_t total_duration = 0;
  uint64_t init_req = 0;
  std::vector<std::pair<uint64_t, uint64_t>> message_durations;
  std::vector<uint64_t> buff_reads;
};

timing_data global_timing;

void signalHandler(int signum) {
  std::cout << "terminate signal (" << signum << ") received.\n";

  // If we get here then the connection is closed gracefully
  // write to file
  std::ofstream timing;
  timing.open("timing.csv");
  for (auto i = global_timing.message_durations.begin();
       i != global_timing.message_durations.end(); ++i) {
    timing << i->first << "," << i->second << "\n";
  }
  timing.close();

  std::ofstream summary;
  summary.open("summary.txt");
  summary << "init req: " << std::to_string(global_timing.init_req) << "\n";
  summary << "closing! after: " << std::to_string(global_timing.total_duration)
          << "\n";
  summary.close();

  exit(signum);
}

// Sends a WebSocket message and prints the response
int main(int argc, char** argv) {
  signal(SIGTERM, signalHandler);

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
    auto const verbose =
        (std::string(argv[3]) == "true" || std::string(argv[3]) == "1") ? true
                                                                        : false;
    auto const text =
        "{\"type\": \"subscribe\", \"product_ids\": [\"BTC-USD\"], "
        "\"channels\": [\"level2\", \"matches\"]}";
    uint64_t seconds_to_epoch = 0;
    uint64_t sec_to_ns = 1000000000;
    int price_digits = 2;
    int qty_digits = 8;

    global_timing.start = std::chrono::high_resolution_clock::now();

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
    auto request = std::chrono::high_resolution_clock::now();
    ws.write(net::buffer(std::string(text)));
    auto recv = std::chrono::high_resolution_clock::now();
    global_timing.init_req =
        std::chrono::duration_cast<std::chrono::nanoseconds>(recv - request)
            .count();

    // This buffer will hold the incoming message
    beast::flat_buffer buffer;

    // Read a message into our buffer
    for (;;) {
      auto buff_read_tic = std::chrono::high_resolution_clock::now();
      ws.read(buffer);
      auto now = std::chrono::high_resolution_clock::now();
      uint64_t exos_time = std::chrono::duration_cast<std::chrono::nanoseconds>(
                               now.time_since_epoch())
                               .count();
      auto buff_read = std::chrono::duration_cast<std::chrono::nanoseconds>(
                           now - buff_read_tic)
                           .count();

      uint64_t elapsedEpoch = exos_time / sec_to_ns;
      int64_t t_ns = exos_time % sec_to_ns;

      if (elapsedEpoch > seconds_to_epoch) {
        seconds_to_epoch = elapsedEpoch;
        Time ore_msg(0, seconds_to_epoch);
        msgpack::sbuffer sbuf;
        msgpack::pack(sbuf, ore_msg);

        if (verbose) {
          msgpack::object_handle oh = msgpack::unpack(sbuf.data(), sbuf.size());
          msgpack::object deserialized = oh.get();
          std::cout << deserialized << std::endl;
        }
      }

      rapidjson::Document j;
      j.Parse(beast::buffers_to_string(buffer.data()).c_str());

      std::string type = j["type"].GetString();

      if (type == "subscriptions") {
        buffer.consume(buffer.size());
        continue;
      } else if (type == "snapshot") {
        auto bids = j["bids"].GetArray();
        auto asks = j["asks"].GetArray();

        for (auto bids_iter = bids.begin(); bids_iter != bids.end();
             ++bids_iter) {
          auto prc = bids_iter->GetArray()[0].GetString();
          auto sz = bids_iter->GetArray()[1].GetString();
          int price_field = str_to_intfield(prc, price_digits);
          int qty_field = str_to_intfield(sz, qty_digits);

          LevelSet ore_msg(14, t_ns, 0, 0, 0, 0, price_field, qty_field, true);
          msgpack::sbuffer sbuf;
          msgpack::pack(sbuf, ore_msg);

          if (verbose) {
            msgpack::object_handle oh =
                msgpack::unpack(sbuf.data(), sbuf.size());
            msgpack::object deserialized = oh.get();
            std::cout << deserialized << std::endl;
          }
        }

        for (auto asks_iter = asks.begin(); asks_iter != asks.end();
             ++asks_iter) {
          auto prc = asks_iter->GetArray()[0].GetString();
          auto sz = asks_iter->GetArray()[1].GetString();
          int price_field = str_to_intfield(prc, price_digits);
          int qty_field = str_to_intfield(sz, qty_digits);

          LevelSet ore_msg(14, t_ns, 0, 0, 0, 0, price_field, qty_field, false);
          msgpack::sbuffer sbuf;
          msgpack::pack(sbuf, ore_msg);

          if (verbose) {
            msgpack::object_handle oh =
                msgpack::unpack(sbuf.data(), sbuf.size());
            msgpack::object deserialized = oh.get();
            std::cout << deserialized << std::endl;
          }
        }

      } else {
        std::string ts = j["time"].GetString();
        uint64_t vendor_time = EpochConverter(ts);
        int64_t vendor_offset = vendor_time - exos_time;

        if (type == "l2update") {
          std::string side =
              rapidjson::Pointer("/changes/0/0").Get(j)->GetString();
          std::string prc =
              rapidjson::Pointer("/changes/0/1").Get(j)->GetString();
          std::string sz =
              rapidjson::Pointer("/changes/0/2").Get(j)->GetString();
          int price_field = str_to_intfield(prc, price_digits);
          int qty_field = str_to_intfield(sz, qty_digits);
          LevelSet ore_msg(14, t_ns, vendor_offset, 0, 0, 0, price_field,
                           qty_field, side == "buy");
          msgpack::sbuffer sbuf;
          msgpack::pack(sbuf, ore_msg);

          if (verbose) {
            msgpack::object_handle oh =
                msgpack::unpack(sbuf.data(), sbuf.size());
            msgpack::object deserialized = oh.get();
            std::cout << deserialized << std::endl;
          }
        }

        // price/size might be the same as from l2,
        // maybe we could cache? or vice versa
        else if (type == "match") {
          std::string side = j["side"].GetString();
          std::string prc = j["price"].GetString();
          std::string sz = j["size"].GetString();
          auto price_field = str_to_intfield(prc, price_digits);
          auto qty_field = str_to_intfield(sz, qty_digits);
          Match ore_msg(11, t_ns, vendor_offset, 0, 0, 0, price_field,
                        qty_field, side == "buy" ? "b" : "s");
          msgpack::sbuffer sbuf;
          msgpack::pack(sbuf, ore_msg);

          if (verbose) {
            msgpack::object_handle oh =
                msgpack::unpack(sbuf.data(), sbuf.size());
            msgpack::object deserialized = oh.get();
            std::cout << deserialized << std::endl;
          }
        }
      }

      // drain buffer
      buffer.consume(buffer.size());
      auto exos_end = std::chrono::high_resolution_clock::now();
      auto mess =
          std::chrono::duration_cast<std::chrono::nanoseconds>(exos_end - now)
              .count();
      global_timing.message_durations.push_back(
          std::make_pair(mess, buff_read));

      //   // // timing data
      //   auto stop = std::chrono::high_resolution_clock::now();
      //   global_timing.total_duration =
      //       std::chrono::duration_cast<std::chrono::nanoseconds>(
      //           stop - global_timing.start)
      //           .count();
    }

    // Close the WebSocket connection
    ws.close(websocket::close_code::normal);
  } catch (std::exception const& e) {
    std::cerr << "Error: " << e.what() << std::endl;
    return EXIT_FAILURE;
  }
  return EXIT_SUCCESS;
}
