
#include <chrono>
#include <msgpack.hpp>

class LevelSet {
 public:
  LevelSet(int idx, uint64_t receive, int vendor_offset, int vendor_seqno,
           int batch, int imnt_id, std::string price, std::string qty,
           bool is_bid)
      : idx_(idx),
        receive_(receive),
        vendor_offset_(vendor_offset),
        vendor_seqno_(vendor_seqno),
        batch_(batch),
        imnt_id_(imnt_id),
        price_(price),
        qty_(qty),
        is_bid_(is_bid) {}

  MSGPACK_DEFINE(idx_, receive_, vendor_offset_, vendor_seqno_, batch_,
                 imnt_id_, price_, qty_, is_bid_)

 private:
  int idx_;
  uint64_t receive_;
  int vendor_offset_;
  int vendor_seqno_;
  int batch_;
  int imnt_id_;
  std::string price_;
  std::string qty_;
  bool is_bid_;
};

class Match {
 public:
  Match(int idx, uint64_t receive, int vendor_offset, int vendor_seqno,
        int batch, int imnt_id, std::string trade_price, std::string qty,
        std::string decorator)
      : idx_(idx),
        receive_(receive),
        vendor_offset_(vendor_offset),
        vendor_seqno_(vendor_seqno),
        batch_(batch),
        imnt_id_(imnt_id),
        trade_price_(trade_price),
        qty_(qty),
        decorator_(decorator) {}

  MSGPACK_DEFINE(idx_, receive_, vendor_offset_, vendor_seqno_, batch_,
                 imnt_id_, trade_price_, qty_, decorator_)

 private:
  int idx_;
  uint64_t receive_;
  int vendor_offset_;
  int vendor_seqno_;
  int batch_;
  int imnt_id_;
  std::string trade_price_;
  std::string qty_;
  std::string decorator_;
};