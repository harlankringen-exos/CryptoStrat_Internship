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
// Example: WebSocket client, asynchronous
// does not have any ssl business
//
//------------------------------------------------------------------------------

#include <boost/asio/strand.hpp>
#include <boost/beast/core.hpp>
#include <boost/beast/websocket.hpp>
#include <chrono>
#include <cstdlib>
#include <functional>
#include <iostream>
#include <memory>
#include <string>

#include "helpers.hpp"
#include "nlohmann/json.hpp"
#include "ore.hpp"

// for convenience
using json = nlohmann::json;

namespace beast = boost::beast;          // from <boost/beast.hpp>
namespace http = beast::http;            // from <boost/beast/http.hpp>
namespace websocket = beast::websocket;  // from <boost/beast/websocket.hpp>
namespace net = boost::asio;             // from <boost/asio.hpp>
using tcp = boost::asio::ip::tcp;        // from <boost/asio/ip/tcp.hpp>

//------------------------------------------------------------------------------

// Report a failure
void fail(beast::error_code ec, char const* what) {
  std::cerr << what << ": " << ec.message() << "\n";
}

// Sends a WebSocket message and prints the response
class session : public std::enable_shared_from_this<session> {
  tcp::resolver resolver_;
  websocket::stream<beast::tcp_stream> ws_;
  beast::flat_buffer buffer_;
  std::string host_;
  bool verbose_;
  std::string text_ =
      "{\"type\": \"subscribe\", \"product_ids\": [\"BTC-USD\"], "
      "\"channels\": [\"level2\", \"matches\"]}";
  int ctr = 0;
  // std::chrono::time_point<std::chrono::high_resolution_clock> start;
  // std::chrono::time_point<std::chrono::high_resolution_clock> stop;

  uint64_t seconds_to_epoch = 0;
  uint64_t sec_to_ns = 1000000000;
  int price_digits = 2;
  int qty_digits = 8;

 public:
  // Resolver and socket require an io_context
  explicit session(net::io_context& ioc)
      : resolver_(net::make_strand(ioc)), ws_(net::make_strand(ioc)) {
    // start = std::chrono::high_resolution_clock::now();
  }

  // Start the asynchronous operation
  void run(char const* host, char const* port, bool verbose) {
    // Save these for later
    host_ = host;
    verbose_ = verbose;

    // Look up the domain name
    resolver_.async_resolve(
        host, port,
        beast::bind_front_handler(&session::on_resolve, shared_from_this()));
  }

  void on_resolve(beast::error_code ec, tcp::resolver::results_type results) {
    if (ec) return fail(ec, "resolve");

    // Set the timeout for the operation
    beast::get_lowest_layer(ws_).expires_after(std::chrono::seconds(30));

    // Make the connection on the IP address we get from a lookup
    beast::get_lowest_layer(ws_).async_connect(
        results,
        beast::bind_front_handler(&session::on_connect, shared_from_this()));
  }

  void on_connect(beast::error_code ec,
                  tcp::resolver::results_type::endpoint_type ep) {
    if (ec) return fail(ec, "connect");

    // Turn off the timeout on the tcp_stream, because
    // the websocket stream has its own timeout system.
    beast::get_lowest_layer(ws_).expires_never();

    // Set suggested timeout settings for the websocket
    ws_.set_option(
        websocket::stream_base::timeout::suggested(beast::role_type::client));

    // Set a decorator to change the User-Agent of the handshake
    ws_.set_option(
        websocket::stream_base::decorator([](websocket::request_type& req) {
          req.set(http::field::user_agent,
                  std::string(BOOST_BEAST_VERSION_STRING) +
                      " websocket-client-async");
        }));

    // Update the host_ string. This will provide the value of the
    // Host HTTP header during the WebSocket handshake.
    // See https://tools.ietf.org/html/rfc7230#section-5.4
    host_ += ':' + std::to_string(ep.port());

    // Perform the websocket handshake
    ws_.async_handshake(
        host_, "/",
        beast::bind_front_handler(&session::on_handshake, shared_from_this()));
  }

  void on_handshake(beast::error_code ec) {
    if (ec) return fail(ec, "handshake");

    // Send the message
    ws_.async_write(
        net::buffer(text_),
        beast::bind_front_handler(&session::on_write, shared_from_this()));
  }

  void on_write(beast::error_code ec, std::size_t bytes_transferred) {
    boost::ignore_unused(bytes_transferred);

    if (ec) return fail(ec, "write");

    // Read a message into our buffer

    ws_.async_read(buffer_, beast::bind_front_handler(&session::on_process,
                                                      shared_from_this()));
  }

  // ORE-ify and msgpack...but asynchronously; should all just be cpu-bound code
  // would it make sense to make asynchronously somehow?
  void on_process(beast::error_code ec, std::size_t bytes_transferred) {
    boost::ignore_unused(bytes_transferred);
    if (ec) return fail(ec, "process");

    ++ctr;

    if (ctr == 10002) {
      // Close the WebSocket connection
      ws_.async_close(
          websocket::close_code::normal,
          beast::bind_front_handler(&session::on_close, shared_from_this()));
    }

    uint64_t exos_time =
        std::chrono::duration_cast<std::chrono::nanoseconds>(
            std::chrono::high_resolution_clock::now().time_since_epoch())
            .count();
    uint64_t elapsedEpoch = exos_time / sec_to_ns;
    int64_t t_ns = exos_time % sec_to_ns;

    json j = json::parse(beast::buffers_to_string(buffer_.data()));
    std::string type = j["type"];

    if (type == "subscriptions") {
      buffer_.consume(buffer_.size());
    } else if (type == "snapshot") {
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

        if (verbose_) {
          msgpack::object_handle oh = msgpack::unpack(sbuf.data(), sbuf.size());
          msgpack::object deserialized = oh.get();
          std::cout << deserialized << std::endl;
        }
      }
    } else {
      std::string ts = j["time"];
      uint64_t vendor_time = EpochConverter(ts);
      int64_t vendor_offset = vendor_time - exos_time;

      if (elapsedEpoch > seconds_to_epoch) {
        seconds_to_epoch = elapsedEpoch;
        Time ore_msg(0, seconds_to_epoch);
        std::array<Time, 1> arr = {ore_msg};
        msgpack::sbuffer sbuf;
        msgpack::pack(sbuf, arr);

        if (verbose_) {
          msgpack::object_handle oh = msgpack::unpack(sbuf.data(), sbuf.size());
          msgpack::object deserialized = oh.get();
          std::cout << deserialized << std::endl;
        }
      }

      if (type == "l2update") {
        int price_field = str_to_intfield(j["changes"][0][1], price_digits);
        int qty_field = str_to_intfield(j["changes"][0][2], qty_digits);
        LevelSet ore_msg(14, t_ns, vendor_offset, 0, 0, 0, price_field,
                         qty_field, j["changes"][0][0] == "buy");
        std::array<LevelSet, 1> arr = {ore_msg};
        msgpack::sbuffer sbuf;
        msgpack::pack(sbuf, arr);

        if (verbose_) {
          msgpack::object_handle oh = msgpack::unpack(sbuf.data(), sbuf.size());
          msgpack::object deserialized = oh.get();
          std::cout << deserialized << std::endl;
        }
      }

      else if (type == "match") {
        auto price_field = str_to_intfield(j["price"], price_digits);
        auto qty_field = str_to_intfield(j["size"], qty_digits);
        Match ore_msg(11, t_ns, vendor_offset, 0, 0, 0, price_field, qty_field,
                      j["side"] == "buy" ? "b" : "s");
        std::array<Match, 1> arr = {ore_msg};
        msgpack::sbuffer sbuf;
        msgpack::pack(sbuf, arr);

        if (verbose_) {
          msgpack::object_handle oh = msgpack::unpack(sbuf.data(), sbuf.size());
          msgpack::object deserialized = oh.get();
          std::cout << deserialized << std::endl;
        }
      }
    }

    // drain buffer
    buffer_.consume(buffer_.size());

    ws_.async_read(buffer_, beast::bind_front_handler(&session::on_process,
                                                      shared_from_this()));
  }

  // void on_read(beast::error_code ec, std::size_t bytes_transferred) {
  //   boost::ignore_unused(bytes_transferred);

  //   ++ctr;

  //   if (ec) return fail(ec, "write");

  //   if (ctr == 10002) {
  //     // Close the WebSocket connection
  //     ws_.async_close(
  //         websocket::close_code::normal,
  //         beast::bind_front_handler(&session::on_close, shared_from_this()));
  //   }

  //   // read another
  //   ws_.async_read(buffer_, beast::bind_front_handler(&session::on_process,
  //                                                     shared_from_this()));
  // }

  void on_close(beast::error_code ec) {
    // stop = std::chrono::high_resolution_clock::now();
    // std::cout << "closing! after: "
    //           << std::to_string(
    //                  std::chrono::duration_cast<std::chrono::nanoseconds>(stop
    //                  -
    //                                                                       start)
    //                      .count())
    //           << std::endl;
    if (ec) return fail(ec, "close");
  }
};

//------------------------------------------------------------------------------

int main(int argc, char** argv) {
  // Check command line arguments.
  if (argc != 4) {
    std::cerr << "Usage: websocket-client-async <host> <port> <text>\n"
              << "Example:\n"
              << "    websocket-client-async echo.websocket.org 80 \"true\n ";
    return EXIT_FAILURE;
  }
  auto const host = argv[1];
  auto const port = argv[2];
  auto const verbose =
      (std::string(argv[3]) == "true" || std::string(argv[3]) == "1") ? true
                                                                      : false;

  // The io_context is required for all I/O
  net::io_context ioc;

  // Launch the asynchronous operation
  std::make_shared<session>(ioc)->run(host, port, verbose);

  // Run the I/O service. The call will return when
  // the socket is closed.
  ioc.run();

  return EXIT_SUCCESS;
}
