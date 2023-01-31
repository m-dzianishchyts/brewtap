# typed: false
# frozen_string_literal: true

# This file was generated by Homebrew Releaser. DO NOT EDIT.
class TestGenerateFormulaEmptyFields < Formula
  desc "NA"
  homepage "https://github.com/Justintime50/test-generate-formula-empty-fields"
  url "https://github.com/Justintime50/test-generate-formula-empty-fields/archive/v0.1.0.tar.gz"
  sha256 "0000000000000000000000000000000000000000000000000000000000000000"

  def install
    bin.install "src/secure-browser-kiosk.sh" => "secure-browser-kiosk"
  end
end
