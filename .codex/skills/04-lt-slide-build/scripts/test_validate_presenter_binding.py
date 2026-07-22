import importlib.util
import unittest
from pathlib import Path


SCRIPT = Path(__file__).with_name("validate_presenter_binding.py")
SPEC = importlib.util.spec_from_file_location("validate_presenter_binding", SCRIPT)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC and SPEC.loader
SPEC.loader.exec_module(MODULE)


PRESENTER = {
    "display_name": "Demo Presenter",
    "bio": "デモ用プロフィール",
    "links": [{"platform": "GitHub", "account": "demo"}],
    "avatar": {"use": False},
    "qr": {"use": False},
}


def profile_html(extra: str = "") -> str:
    return f"""
    <section class="slide" data-role="profile">
      <div class="zone title-zone" data-zone="title"><span>PROFILE</span><h1>自己紹介</h1></div>
      <div class="zone profile-avatar" data-zone="visual"><div class="avatar-card"><img alt="avatar"></div></div>
      <div class="zone profile-text" data-zone="text">
        <div class="profile-copy"><h2>Demo Presenter</h2><p>デモ用プロフィール</p>
          <ul><li><strong>GitHub</strong><span>demo</span></li></ul>
        </div>
      </div>
      {extra}
      <div class="zone footer-zone" data-zone="footer"><span>PROFILE</span><span>1 / 1</span></div>
    </section>
    """


def validate_markup(markup: str):
    original = MODULE.Path.read_text
    MODULE.Path.read_text = lambda self, encoding="utf-8": markup
    try:
        return MODULE.validate(Path("deck.html"), Path("presenter.json"), PRESENTER)
    finally:
        MODULE.Path.read_text = original


class PresenterBindingTests(unittest.TestCase):
    def test_accepts_presenter_json_only_profile(self):
        errors = validate_markup(profile_html())
        self.assertEqual([], errors)

    def test_rejects_topic_specific_conclusion(self):
        markup = profile_html(
            '<div class="zone conclusion-bar" data-zone="conclusion">JSONにないメッセージ</div>'
        )
        errors = validate_markup(markup)
        self.assertTrue(any("追加メッセージ" in error or "表示領域" in error for error in errors))


if __name__ == "__main__":
    unittest.main()
