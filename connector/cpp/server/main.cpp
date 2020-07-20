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
// Example: WebSocket server, synchronous
//
//------------------------------------------------------------------------------

#include <boost/asio/ip/tcp.hpp>
#include <boost/beast/core.hpp>
#include <boost/beast/websocket.hpp>
#include <cstdlib>
#include <functional>
#include <iostream>
#include <string>
#include <thread>

#include "nlohmann/json.hpp"

// for convenience
using json = nlohmann::json;

namespace beast = boost::beast;          // from <boost/beast.hpp>
namespace http = beast::http;            // from <boost/beast/http.hpp>
namespace websocket = beast::websocket;  // from <boost/beast/websocket.hpp>
namespace net = boost::asio;             // from <boost/asio.hpp>
using tcp = boost::asio::ip::tcp;        // from <boost/asio/ip/tcp.hpp>

//------------------------------------------------------------------------------

// Echoes back all received WebSocket messages
void do_session(tcp::socket& socket) {
  try {
    // Construct the stream by moving in the socket
    websocket::stream<tcp::socket> ws{std::move(socket)};

    // Set a decorator to change the Server of the handshake
    ws.set_option(
        websocket::stream_base::decorator([](websocket::response_type& res) {
          res.set(http::field::server, std::string(BOOST_BEAST_VERSION_STRING) +
                                           " websocket-server-sync");
        }));

    // Accept the websocket handshake
    ws.accept();

    for (;;) {
      // This buffer will hold the incoming message
      beast::flat_buffer buffer;

      std::cout << "reading" << std::endl;
      // Read a message
      ws.read(buffer);

      if (beast::buffers_to_string(buffer.data()).size() > 1) {
        std::cout << "beginning deluge\n";
        std::string match =
            "{\"type\":\"match\",\"trade_id\":14587419,\"maker_order_id\":"
            "\"91b59a7c-6a07-4039-9536-21daf3cb3282\",\"taker_order_id\":"
            "\"47888661-47cc-4af6-a26e-ea359b236b1b\",\"side\":\"buy\","
            "\"size\":\"0.0659\",\"price\":\"9120.8\",\"product_id\":\"BTC-"
            "USD\",\"sequence\":180754935,\"time\":\"2020-06-30T19:10:24."
            "602001Z\"}";
        std::string update =
            "{\"changes\":[[\"buy\",\"9095.58\",\"0.00000000\"]],\"product_"
            "id\":\"BTC-USD\",\"time\":\"2020-06-30T19:10:25.756751Z\","
            "\"type\":\"l2update\"}";
        bool alternating = true;
        for (int i = 0; i != 10000; ++i) {
          std::cout << i << std::endl;
          if (alternating) {
            ws.write(net::buffer(match));
          } else {
            ws.write(net::buffer(update));
          }
          alternating = !alternating;
        }

        // // Echo the message back
        // ws.text(ws.got_text());
        // ws.write(buffer.data());
        // std::cout << "server: " << beast::make_printable(buffer.data())
        //           << std::endl;
      }
    }
  } catch (beast::system_error const& se) {
    // This indicates that the session was closed
    if (se.code() != websocket::error::closed)
      std::cerr << "Error: " << se.code().message() << std::endl;
  } catch (std::exception const& e) {
    std::cerr << "Error: " << e.what() << std::endl;
  }
}

//------------------------------------------------------------------------------

int main(int argc, char* argv[]) {
  try {
    // Check command line arguments.
    if (argc != 3) {
      std::cerr << "Usage: websocket-server-sync <address> <port>\n"
                << "Example:\n"
                << "    websocket-server-sync 0.0.0.0 8080\n";
      return EXIT_FAILURE;
    }
    auto const address = net::ip::make_address(argv[1]);
    auto const port = static_cast<unsigned short>(std::atoi(argv[2]));

    // The io_context is required for all I/O
    net::io_context ioc{1};

    // The acceptor receives incoming connections
    tcp::acceptor acceptor{ioc, {address, port}};
    for (;;) {
      std::cout << "loop" << std::endl;
      // This will receive the new connection
      tcp::socket socket{ioc};

      // Block until we get a connection
      acceptor.accept(socket);

      // Launch the session, transferring ownership of the socket
      std::thread{std::bind(&do_session, std::move(socket))}.detach();
    }
  } catch (const std::exception& e) {
    std::cerr << "Error: " << e.what() << std::endl;
    return EXIT_FAILURE;
  }
}
