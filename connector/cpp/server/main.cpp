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
        std::string subs =
            "{\"type\":\"subscriptions\",\"channels\":[{\"name\":\"heartbeat\","
            "\"product_ids\":[\"BTC-USD\"]},{\"name\":\"level2\",\"product_"
            "ids\":[\"BTC-USD\"]}]}";
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
        std::string snapshot =
            "{\"type\":\"snapshot\",\"product_id\":\"BTC-USD\",\"asks\":[["
            "\"9134.77\",\"2865.97630000\"],[\"9134.78\",\"4771.00000000\"],["
            "\"9134.79\",\"6020.00000000\"],[\"9134.80\",\"6989.00000000\"],["
            "\"9134.81\",\"7781.00000000\"],[\"9134.82\",\"8450.00000000\"],["
            "\"9134.83\",\"9030.00000000\"],[\"9134.84\",\"9542.00000000\"],["
            "\"9142.08\",\"14.83710000\"],[\"9142.42\",\"0.12940000\"],[\"9143."
            "47\",\"0.80680000\"],[\"9153.66\",\"0.03250000\"],[\"9166.22\","
            "\"0.02830000\"],[\"9168.62\",\"0.06490000\"],[\"9169.17\",\"0."
            "03200000\"],[\"9169.99\",\"0.09390000\"],[\"9171.22\",\"0."
            "09390000\"],[\"9176.32\",\"0.03960000\"],[\"9176.59\",\"156."
            "27500000\"],[\"9176.74\",\"0.06880000\"],[\"9180.96\",\"0."
            "03290000\"],[\"9191.88\",\"0.00100000\"],[\"9299.99\",\"0."
            "00500000\"],[\"9423.42\",\"9999.00000000\"],[\"9432.70\",\"0."
            "00670414\"],[\"9961.44\",\"0.09080013\"],[\"11999.99\",\"0."
            "06000000\"],[\"58000.00\",\"1.88000000\"],[\"200000.00\",\"0."
            "50000000\"],[\"1000000.00\",\"100000.00000000\"],[\"8000070.30\","
            "\"0.02570000\"],[\"9999999.02\",\"0.00100000\"],[\"10000000.00\","
            "\"1.00000000\"],[\"11099891.00\",\"0.05000000\"]],\"bids\":[["
            "\"9134.75\",\"2968.87610000\"],[\"9134.74\",\"4771.00000000\"],["
            "\"9134.73\",\"6020.00000000\"],[\"9134.72\",\"6989.00000000\"],["
            "\"9134.71\",\"7781.00000000\"],[\"9134.70\",\"8450.00000000\"],["
            "\"9134.69\",\"9030.00000000\"],[\"9134.68\",\"9542.00000000\"],["
            "\"9133.83\",\"0.02220000\"],[\"9117.40\",\"0.06760000\"],[\"9114."
            "22\",\"0.02760000\"],[\"9111.01\",\"0.02830000\"],[\"9110.86\","
            "\"0.02830000\"],[\"9083.00\",\"0.00160000\"],[\"9075.38\",\"0."
            "05600000\"],[\"9002.86\",\"0.00300000\"],[\"9000.01\",\"0."
            "00600000\"],[\"8964.07\",\"0.17800000\"],[\"8900.00\",\"0."
            "03000000\"],[\"8898.01\",\"0.04594706\"],[\"8611.00\",\"1."
            "05598206\"],[\"8500.00\",\"12.00500000\"],[\"8150.26\",\"0."
            "11097805\"],[\"8000.00\",\"0.47000000\"],[\"7597.68\",\"0."
            "01100000\"],[\"7400.00\",\"1.00000000\"],[\"5031.00\",\"0."
            "30000000\"],[\"5000.00\",\"0.02450000\"],[\"3660.00\",\"203279."
            "99300000\"],[\"3500.00\",\"25000.00000000\"],[\"3000.00\",\"0."
            "21583329\"],[\"2962.53\",\"0.01100000\"],[\"2000.00\",\"220000."
            "48000000\"],[\"1900.00\",\"1.00000000\"],[\"1090.00\",\"12."
            "00000000\"],[\"1000.00\",\"4.52000000\"],[\"900.00\",\"0."
            "00100000\"],[\"500.00\",\"100.00300000\"],[\"280.00\",\"1."
            "00000000\"],[\"200.00\",\"0.18000000\"],[\"104.50\",\"1."
            "85300000\"],[\"100.00\",\"114.94500000\"],[\"75.00\",\"6."
            "00000000\"],[\"30.00\",\"1934.99132469\"],[\"20.00\",\"10."
            "00000000\"],[\"15.00\",\"5.00000000\"],[\"10.00\",\"107063."
            "84702300\"],[\"7.13\",\"0.00100000\"],[\"4.00\",\"2.00000000\"],["
            "\"2.00\",\"102.53000000\"],[\"1.12\",\"1.00000000\"],[\"1.11\","
            "\"0.02600000\"],[\"1.00\",\"1001054.20200000\"],[\"0.83\",\"1."
            "00000000\"],[\"0.20\",\"0.00400000\"],[\"0.19\",\"1.00000000\"],["
            "\"0.16\",\"12.00000000\"],[\"0.10\",\"0.18330000\"],[\"0.01\","
            "\"10390.79441258\"]]}";
        bool alternating = true;

        ws.write(net::buffer(subs));
        // ws.write(net::buffer(snapshot));
        for (int i = 0; i != 9998; ++i) {
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
