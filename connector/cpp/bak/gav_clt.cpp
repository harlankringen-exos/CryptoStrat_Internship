#include <boost/asio/connect.hpp>
#include <boost/asio/ip/tcp.hpp>
#include <boost/asio/ssl/stream.hpp>
#include <boost/beast/core.hpp>
#include <boost/beast/ssl.hpp>
#include <boost/beast/websocket.hpp>
#include <boost/beast/websocket/ssl.hpp>
#include <chrono>
#include <cstdlib>
#include <iostream>
#include <string>

namespace beast = boost::beast;          // from <boost/beast.hpp>
namespace http = beast::http;            // from <boost/beast/http.hpp>
namespace websocket = beast::websocket;  // from <boost/beast/websocket.hpp>
namespace net = boost::asio;             // from <boost/asio.hpp>
namespace ssl = boost::asio::ssl;        // from <boost/asio/ssl.hpp>
using tcp = boost::asio::ip::tcp;        // from <boost/asio/ip/tcp.hpp>
using namespace std::chrono;

struct result_t {
  std::string msg;
  steady_clock::time_point ts;
};

// Sends a WebSocket message and prints the response
std::function<result_t()> get_generator() {
  try {
    // Check command line arguments.
    struct generator_t {
      generator_t() {
        auto const host = "ws-feed.prime.coinbase.com";
        auto const port = std::string("443");
        auto const text =
            "{\"type\": \"subscribe\", \"product_ids\": [\"BTC-USD\"], "
            "\"channels\": [\"level2\"]}";

        // The io_context is required for all I/O
        net::io_context ioc;

        // The SSL context is required, and holds certificates
        ssl::context ctx(ssl::context::tlsv12_client);

        // This holds the root certificate used for verification
        //       load_root_certificates(ctx);
        //
        // Verify the remote server's certificate
        ctx.set_verify_mode(ssl::verify_none);

        // These objects perform our I/O
        tcp::resolver resolver(ioc);
        ws = new websocket::stream<beast::ssl_stream<tcp::socket>>(ioc, ctx);
        if (!SSL_set_tlsext_host_name(ws->next_layer().native_handle(), host)) {
          boost::system::error_code ec{static_cast<int>(::ERR_get_error()),
                                       boost::asio::error::get_ssl_category()};
          throw boost::system::system_error{ec};
        }
        std::cerr << "made websocket" << std::endl;
        // Look up the domain name
        auto const results = resolver.resolve(host, port);
        std::cerr << "results" << std::endl;

        // Make the connection on the IP address we get from a lookup
        auto ep = net::connect(ws->next_layer().next_layer(), results.begin(),
                               results.end());

        std::cerr << "Connected" << std::endl;
        // Perform the SSL handshake
        ws->next_layer().handshake(ssl::stream_base::client);
        std::cerr << "handshake" << std::endl;

        // Set a decorator to change the User-Agent of the handshake
        ws->set_option(
            websocket::stream_base::decorator([](websocket::request_type& req) {
              req.set(http::field::user_agent,
                      std::string(BOOST_BEAST_VERSION_STRING) +
                          " websocket-client-coro");
            }));

        // Perform the websocket handshake
        ws->handshake("ws-feed.prime.coinbase.com:443", "/");

        // Send the message
        ws->write(net::buffer(std::string(text)));
      }
      result_t operator()() {
        beast::flat_buffer buffer;
        // Read a message into our buffer
        ws->read(buffer);
        result_t res;
        res.msg = boost::beast::buffers_to_string(buffer.data());
        res.ts = steady_clock::now();
        return res;
      }

     private:
      websocket::stream<beast::ssl_stream<tcp::socket>>* ws;
    } generator;
    return generator;
  } catch (std::exception const& e) {
    std::cerr << "Error: " << e.what() << std::endl;
    return NULL;
  }
  return NULL;
}

int main(int argc, char** argv) {
  auto const generator = get_generator();
  result_t msg;
  steady_clock::time_point last_msg = steady_clock::now();
  for (;;) {
    steady_clock::time_point last_msg = steady_clock::now();
    msg = generator();
    steady_clock::time_point msg1 = steady_clock::now();
    auto time_span = duration_cast<nanoseconds>(msg1 - last_msg);
    std::cout << std::fixed << (time_span.count()) << std::endl;
    //        std::cout << msg.msg << std::endl;
  }
}
