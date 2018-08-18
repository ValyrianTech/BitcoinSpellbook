#!/usr/bin/python
# -*- coding: utf-8 -*-

import pytest
import random
from helpers.conversionhelpers import btc2satoshis


class TestConversionHelpers(object):

    @pytest.mark.parametrize('btc, expected', [
        ['0.00000001', 1],
        [0.00000001, 1],
        ['1.00000001', 100000001],
        [1.00000001, 100000001],
        ['1.00010000', 100010000],
        [1.00010000, 100010000],
        ['1.0001', 100010000],
        [1.0001, 100010000],
        ['1', 100000000],
        [1, 100000000],
        ['1.00000000', 100000000],
        [1.00000000, 100000000],
        ["13.21909301", 1321909301]
    ])
    def test_btc2satoshis(self, btc, expected):
        assert btc2satoshis(btc=btc) == expected
        assert type(btc2satoshis(btc=btc)) in [int, long]

    def test_btc2satoshis_with_random_data(self):
        for _ in range(10000):
            random_satoshis = random.randint(1, 1000000000000)
            btc = str(random_satoshis/1e8)
            assert btc2satoshis(btc=btc) == random_satoshis

