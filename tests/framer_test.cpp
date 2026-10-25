#include <cassert>
#include <cstring>
#include "../firmware/DevPulse/LineFramer.h"

int main() {
  LineFramer<8> framer;
  using Result = LineFramer<8>::Result;
  assert(framer.push('\n') == Result::Pending);
  for (char c : "abcdefg") {
    if (c) assert(framer.push(c) == Result::Pending);
  }
  assert(framer.push('\r') == Result::Pending);
  assert(framer.push('\n') == Result::Ready);
  assert(framer.size() == 7);
  assert(std::strcmp(framer.data(), "abcdefg") == 0);
  for (int i = 0; i < 20; i++) framer.push('x');
  assert(framer.push('\n') == Result::Discarded);
  framer.push('{');
  framer.push('}');
  assert(framer.push('\n') == Result::Ready);
  assert(std::strcmp(framer.data(), "{}") == 0);
  framer.push('a');
  assert(framer.push('\n') == Result::Ready);
  framer.push('b');
  assert(framer.push('\n') == Result::Ready);
  assert(std::strcmp(framer.data(), "b") == 0);
}
