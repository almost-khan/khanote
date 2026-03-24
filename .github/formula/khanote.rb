class Khanote < Formula
  include Language::Python::Virtualenv

  desc "Universal research workflow kit connecting vibe coding tools with Obsidian"
  homepage "https://github.com/almost-khan/khanote"
  url "https://pypi.io/packages/source/k/khanote/khanote-0.1.0.tar.gz"
  sha256 "PLACEHOLDER"
  license "MIT"

  depends_on "python@3.12"

  # Dependencies will be auto-populated after first PyPI release.
  # Run: poet khanote
  # to generate the resource blocks.

  def install
    virtualenv_install_with_resources
  end

  test do
    assert_match "khanote", shell_output("#{bin}/khanote --help")
  end
end
