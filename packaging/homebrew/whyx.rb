# frozen_string_literal: true

class whyx < Formula
  desc "Code navigation and dynamic tracing CLI"
  homepage "https://github.com/mrakbook/whyx"
0.0.7  # placeholder; update_formula.sh will bump this

  on_macos do
    if Hardware::CPU.arm?
      url "https://github.com/mrakbook/whyx/releases/download/release/#{version}/whyx_#{version}_darwin_arm64.tar.gz"
      sha256 "<REPLACE_WITH_SHA256_ARM64>"
    else
      url "https://github.com/mrakbook/whyx/releases/download/release/#{version}/whyx_#{version}_darwin_x86_64.tar.gz"
      sha256 "<REPLACE_WITH_SHA256_X86_64>"
    end
  end

  def install
    bin.install "whyx"
  end

  test do
    out = shell_output("#{bin}/whyx --help")
    assert_match "whyx", out
  end
end
