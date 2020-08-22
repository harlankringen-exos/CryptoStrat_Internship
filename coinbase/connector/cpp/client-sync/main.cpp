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
// meant to connect to cpp/server example
// lacks a lot of ssl junk
//
//------------------------------------------------------------------------------

//[example_websocket_client

#include <boost/asio/connect.hpp>
#include <boost/asio/ip/tcp.hpp>
#include <boost/beast/core.hpp>
#include <boost/beast/websocket.hpp>
#include <chrono>
#include <csignal>
#include <cstdlib>
#include <fstream>
#include <iostream>
#include <string>
#include <tuple>
#include <vector>

#include "helpers.hpp"
//#include "nlohmann/json.hpp"
#include "ore.hpp"

// // for convenience
// using json = nlohmann::json;
#include "rapidjson/document.h"
#include "rapidjson/pointer.h"

namespace beast = boost::beast;          // from <boost/beast.hpp>
namespace http = beast::http;            // from <boost/beast/http.hpp>
namespace websocket = beast::websocket;  // from <boost/beast/websocket.hpp>
namespace net = boost::asio;             // from <boost/asio.hpp>
using tcp = boost::asio::ip::tcp;        // from <boost/asio/ip/tcp.hpp>

struct timing_data {
  std::chrono::high_resolution_clock::time_point start;
  uint64_t total_duration = 0;
  uint64_t init_req = 0;
  std::vector<std::tuple<std::string, uint64_t, uint64_t>>
      message_durations;  // msg type, processing duration, buff read
};

timing_data global_timing;

void signalHandler(int signum) {
  std::cout << "terminate signal (" << signum << ") received.\n";

  // If we get here then the connection is closed gracefully
  // write to file
  std::ofstream timing;
  timing.open("timing.csv");
  timing << "msg_type,processing_time_ns,buff_read_ns\n";
  for (auto i = global_timing.message_durations.begin();
       i != global_timing.message_durations.end(); ++i) {
    timing << std::get<0>(*i) << "," << std::get<1>(*i) << ","
           << std::get<2>(*i) << "\n";
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

int main(int argc, char** argv) {
  signal(SIGTERM, signalHandler);

  try {
    // Check command line arguments.
    // verbose is a bool that prints desserialized messages to stdout if set
    // set at command line as "true" or "1"
    if (argc != 4) {
      std::cerr << "Usage: websocket-client-sync <host> <port> <verbose?>\n"
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

    // // timing data
    // auto start = std::chrono::high_resolution_clock::now();
    // uint64_t total_duration = 0;
    // uint64_t init_req = 0;
    // std::vector<uint64_t> message_duration;
    // std::vector<uint64_t> buff_reads;

    uint64_t seconds_to_epoch = 0;
    uint64_t sec_to_ns = 1000000000;
    int price_digits = 2;
    int qty_digits = 8;
    global_timing.start = std::chrono::high_resolution_clock::now();

    // The io_context is required for all I/O
    net::io_context ioc;

    // These objects perform our I/O
    tcp::resolver resolver{ioc};
    websocket::stream<tcp::socket> ws{ioc};

    // Look up the domain name
    auto const results = resolver.resolve(host, port);

    // Make the connection on the IP address we get from a lookup
    auto ep = net::connect(ws.next_layer(), results);

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

    // This buffer will hold the incoming message
    beast::flat_buffer buffer;

    // Read a message into our buffer
    int actual_msgs = 0;

    // Send the message
    auto request = std::chrono::high_resolution_clock::now();
    ws.write(net::buffer(std::string(text)));
    auto recv = std::chrono::high_resolution_clock::now();
    global_timing.init_req =
        std::chrono::duration_cast<std::chrono::nanoseconds>(recv - request)
            .count();

    for (;;) {
      // don't count subscriptions and snapshot in the 10000
      if (actual_msgs == 10000) {
        break;
      }
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
      // std::cout << "exos time etc:\n"
      //           << std::to_string(exos_time) << " "
      //           << std::to_string(elapsedEpoch) << " " <<
      //           std::to_string(t_ns)
      //           << std::endl;
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
        // timing information used by both l2 and match
        ++actual_msgs;
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
                           qty_field, j["changes"][0][0] == "buy");
          msgpack::sbuffer sbuf;
          msgpack::pack(sbuf, ore_msg);

          if (verbose) {
            msgpack::object_handle oh =
                msgpack::unpack(sbuf.data(), sbuf.size());
            msgpack::object deserialized = oh.get();
            std::cout << deserialized << std::endl;
          }
        }

        else if (type == "match") {
          std::string side = j["side"].GetString();
          std::string prc = j["price"].GetString();
          std::string sz = j["size"].GetString();
          auto price_field = str_to_intfield(prc, price_digits);
          auto qty_field = str_to_intfield(sz, qty_digits);
          Match ore_msg(11, t_ns, vendor_offset, 0, 0, 0, price_field,
                        qty_field, j["side"] == "buy" ? "b" : "s");
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
          std::make_tuple(type, mess, buff_read));
    }

    std::raise(SIGTERM);

    // // // timing data
    // auto stop = std::chrono::high_resolution_clock::now();
    // total_duration =
    //     std::chrono::duration_cast<std::chrono::nanoseconds>(stop - start)
    //         .count();
    // std::cout << "closing! after: " << std::to_string(total_duration)
    //           << std::endl;
    // std::cout << "init req: " << std::to_string(init_req) << std::endl;
    // std::cout << "message durations: " << std::endl;
    // for (auto i = message_duration.begin(); i != message_duration.end(); ++i)
    // {
    //   std::cout << std::to_string(*i) << std::endl;
    // }
    // std::cout << "buff reads: " << std::endl;
    // for (auto i = buff_Reads.begin(); i != buff_reads.end(); ++i) {
    //   std::cout << std::to_string(*i) << std::endl;
    // }

    // Close the WebSocket connection
    ws.close(websocket::close_code::normal);
  } catch (std::exception const& e) {
    std::cerr << "Error: " << e.what() << std::endl;
    return EXIT_FAILURE;
  }
  return EXIT_SUCCESS;
}
