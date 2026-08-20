#!/usr/bin/env python3
from __future__ import annotations

import unittest

from validate_animation_structure import validate


def deck(body: str) -> str:
    return (
        '<div class="deck"><section class="slide" data-slide-id="s06">'
        '<h1 class="slide-title" data-anim="fade" data-step="0">Title</h1>'
        + body
        + '<div class="conclusion-bar" data-anim="rise" data-step="3" '
        'data-reveal-item="true" data-reveal-group="s06-conclusion" '
        'data-reading-order="1" data-sequence-mode="staged" data-motion-reason="conclusion">Conclusion</div>'
        '</section></div>'
    )


class AnimationStructureTests(unittest.TestCase):
    def test_profile_without_topic_conclusion_passes(self) -> None:
        html = (
            '<div class="deck"><section class="slide" data-slide-id="s02" data-role="profile">'
            '<h1 class="slide-title" data-static-intentional="true">自己紹介</h1>'
            '<div class="avatar-card" data-static-intentional="true"><img alt="avatar"></div>'
            '<div class="profile-copy" data-static-intentional="true">Presenter data</div>'
            '<div class="qr-card" data-static-intentional="true"><img alt="qr"></div>'
            '</section></div>'
        )
        errors, _ = validate(html)
        self.assertEqual([], errors)

    def test_non_profile_without_conclusion_fails(self) -> None:
        html = (
            '<div class="deck"><section class="slide" data-slide-id="s03" data-role="explanation">'
            '<h1 class="slide-title" data-static-intentional="true">Title</h1>'
            '</section></div>'
        )
        errors, _ = validate(html)
        self.assertTrue(any("conclusion element is missing" in error for error in errors))

    def test_complete_numbered_sequence_passes(self) -> None:
        html = deck(
            '<div class="flow-node" data-anim="rise" data-step="1" '
            'data-reveal-item="true" data-reveal-group="s06-flow" '
            'data-reading-order="1" data-sequence-mode="item-by-item" data-motion-reason="ordered item">01</div>'
            '<div class="flow-node" data-anim="rise" data-step="2" '
            'data-reveal-item="true" data-reveal-group="s06-flow" '
            'data-reading-order="2" data-sequence-mode="item-by-item" data-motion-reason="ordered item">02</div>'
        )
        errors, _ = validate(html)
        self.assertEqual([], errors)

    def test_partially_unassigned_siblings_fail(self) -> None:
        html = deck(
            '<div class="flow-node" data-anim="rise" data-step="1" '
            'data-reveal-item="true" data-reveal-group="s06-flow" '
            'data-reading-order="1" data-sequence-mode="item-by-item" data-motion-reason="ordered item">01</div>'
            '<div class="flow-node">02 visible too early</div>'
            '<div class="flow-node" data-anim="rise" data-step="2" '
            'data-reveal-item="true" data-reveal-group="s06-flow" '
            'data-reading-order="2" data-sequence-mode="item-by-item" data-motion-reason="ordered item">03</div>'
        )
        errors, _ = validate(html)
        self.assertTrue(any("neither animated nor data-static-intentional" in error for error in errors))

    def test_reversed_semantic_order_fails(self) -> None:
        html = deck(
            '<div class="flow-node" data-anim="rise" data-step="2" '
            'data-reveal-item="true" data-reveal-group="s06-flow" '
            'data-reading-order="1" data-sequence-mode="item-by-item" data-motion-reason="ordered item">01</div>'
            '<div class="flow-node" data-anim="rise" data-step="1" '
            'data-reveal-item="true" data-reveal-group="s06-flow" '
            'data-reading-order="2" data-sequence-mode="item-by-item" data-motion-reason="ordered item">02</div>'
        )
        errors, _ = validate(html)
        self.assertTrue(any("steps must increase" in error for error in errors))

    def test_duplicate_style_attributes_fail(self) -> None:
        html = deck(
            '<div class="flow-node" style="left:0" style="opacity:1" data-anim="rise" data-step="1" '
            'data-reveal-item="true" data-reveal-group="s06-flow" '
            'data-reading-order="1" data-sequence-mode="item-by-item" data-motion-reason="ordered item">01</div>'
            '<div class="flow-node" data-anim="rise" data-step="2" '
            'data-reveal-item="true" data-reveal-group="s06-flow" '
            'data-reading-order="2" data-sequence-mode="item-by-item" data-motion-reason="ordered item">02</div>'
        )
        errors, _ = validate(html)
        self.assertTrue(any("duplicate 'style'" in error for error in errors))


if __name__ == "__main__":
    unittest.main()
