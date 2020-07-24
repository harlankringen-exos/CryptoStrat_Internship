
// Returns number of days since civil 1970-01-01.  Negative values indicate
//    days prior to 1970-01-01.
// Preconditions:  y-m-d represents a date in the civil (Gregorian) calendar
//                 m is in [1, 12]
//                 d is in [1, last_day_of_month(y, m)]
//                 y is "approximately" in
//                   [numeric_limits<Int>::min()/366,
//                   numeric_limits<Int>::max()/366]
//                 Exact range of validity is:
//                 [civil_from_days(numeric_limits<Int>::min()),
//                  civil_from_days(numeric_limits<Int>::max()-719468)]
// http://howardhinnant.github.io/date_algorithms.html#days_from_civil

#include <math.h>
#include <cstdint>
#include <limits>
#include <string>

uint64_t day_ns = 8.64e13;
uint64_t hour_ns = 3.6e12;
uint64_t min_ns = 6.e10;
uint64_t sec_ns = 1.e9;

template <class Int>
constexpr Int days_from_civil(Int y, unsigned m, unsigned d) noexcept {
  static_assert(
      std::numeric_limits<unsigned>::digits >= 18,
      "This algorithm has not been ported to a 16 bit unsigned integer");
  static_assert(
      std::numeric_limits<Int>::digits >= 20,
      "This algorithm has not been ported to a 16 bit signed integer");
  y -= m <= 2;
  const Int era = (y >= 0 ? y : y - 399) / 400;
  const unsigned yoe = static_cast<unsigned>(y - era * 400);  // [0, 399]
  const unsigned doy =
      (153 * (m + (m > 2 ? -3 : 9)) + 2) / 5 + d - 1;          // [0, 365]
  const unsigned doe = yoe * 365 + yoe / 4 - yoe / 100 + doy;  // [0, 146096]
  return era * 146097 + static_cast<Int>(doe) - 719468;
}

int read2(std::string const& str, int pos) {
  return (str[pos] - '0') * 10 + (str[pos + 1] - '0');
}

int read4(std::string const& str, int pos) {
  return (str[pos] - '0') * 1000 + (str[pos + 1] - '0') * 100 +
         (str[pos + 2] - '0') * 10 + (str[pos + 3] - '0');
}

int read6(std::string const& str, int pos) {
  return (str[pos] - '0') * 100000 + (str[pos + 1] - '0') * 10000 +
         (str[pos + 2] - '0') * 1000 + (str[pos + 3] - '0') * 100 +
         (str[pos + 4] - '0') * 10 + (str[pos + 5] - '0');
}

// yyyy-mm-dd hh:MM:ss -> count of non-leap seconds since 1970-01-01 00:00:00
// UTC 0123456789012345678

// this should return the number of nanoseconds from the given
// datestr to 1970 01 01
long long EpochConverter(std::string const& str) {
  auto y = read4(str, 0);
  auto m = read2(str, 5);
  auto d = read2(str, 8);
  auto h = read2(str, 11);
  auto M = read2(str, 14);
  auto s = read2(str, 17);
  auto us = read6(str, 20);
  return days_from_civil(y, m, d) * day_ns + h * hour_ns + M * min_ns +
         s * sec_ns + us * 1000;
}

// this can't be right
int str_to_intfield(std::string s, int ndigits) {
  // assert ndigits >= 0
  auto x = s.find(".");
  if (x == std::string::npos) {
    return stof(s) * (pow(10, ndigits));
  } else {
    int span = s.size() - 1;
    while (s[span] == 0) {
      --span;
    }
    try {
      s.erase(span, s.size());
    } catch (...) {
      std::cout << "error: (" << s << ") " << std::to_string(span) << std::endl;
    }
    auto n = s.size();
    // assert n - x - 1 <= ndigits, f'{n - x},{ndigits}'
    try {
      auto ans = stof(s.erase(x, 1)) * pow(10, (ndigits - n + x + 1));
      return ans;
    } catch (...) {
      std::cout << "second error: (" << s << ") " << std::to_string(span)
                << std::endl;
    }
    return -1;
  }
}
