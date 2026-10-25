#pragma once

#include <stddef.h>

template <size_t Capacity>
class LineFramer {
 public:
  enum class Result { Pending, Ready, Discarded };

  Result push(char c) {
    if (c == '\n') {
      const bool dropped = overflow_;
      completedSize_ = used_;
      buffer_[used_] = '\0';
      used_ = 0;
      overflow_ = false;
      if (dropped) return Result::Discarded;
      return completedSize_ ? Result::Ready : Result::Pending;
    }
    if (c == '\r') return Result::Pending;
    if (!overflow_) {
      if (used_ < Capacity - 1) buffer_[used_++] = c;
      else overflow_ = true;
    }
    return Result::Pending;
  }

  const char* data() const { return buffer_; }
  size_t size() const { return completedSize_; }

 private:
  static_assert(Capacity > 1, "Frame needs space for a terminator");
  char buffer_[Capacity] = {};
  size_t used_ = 0;
  size_t completedSize_ = 0;
  bool overflow_ = false;
};
