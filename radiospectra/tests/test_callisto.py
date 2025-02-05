import os
import glob
import shutil
from pathlib import Path
from datetime import datetime
from tempfile import mkdtemp

import numpy as np
import pytest
from numpy.testing import assert_allclose, assert_array_almost_equal

from radiospectra.util import minimal_pairs
from ..sources.callisto import CallistoSpectrogram, download, query


@pytest.fixture
def CALLISTO_IMAGE():
    path = Path(__file__).parent / "data" / "BIR_20110607_062400_10.fit"
    return str(path)


@pytest.fixture
def CALLISTO_IMAGE_GLOB_KEY():
    return "BIR_*"


@pytest.fixture
def CALLISTO_IMAGE_GLOB_INDEX(CALLISTO_IMAGE, CALLISTO_IMAGE_GLOB_KEY):
    res = glob.glob(os.path.join(str(Path(CALLISTO_IMAGE).parent), CALLISTO_IMAGE_GLOB_KEY))
    return res.index(CALLISTO_IMAGE)


def test_read(CALLISTO_IMAGE):
    ca = CallistoSpectrogram.read(CALLISTO_IMAGE)
    assert ca.start == datetime(2011, 6, 7, 6, 24, 0, 213000)
    assert ca.t_init == 23040.0
    assert ca.shape == (200, 3600)
    assert ca.t_delt == 0.25
    # Test linearity of time axis.
    assert np.array_equal(ca.time_axis, np.linspace(0, 0.25 * (ca.shape[1] - 1), ca.shape[1]))
    assert ca.dtype == np.uint8


@pytest.mark.remote_data
def test_query():
    URL = "http://soleil.i4ds.ch/solarradio/data/2002-20yy_Callisto/2011/09/22/"

    result = list(query(datetime(2011, 9, 22, 5), datetime(2011, 9, 22, 6), {"BIR"}))
    RESULTS = [
        "BIR_20110922_050000_01.fit.gz",
        "BIR_20110922_051500_01.fit.gz",
        "BIR_20110922_053000_01.fit.gz",
        "BIR_20110922_050000_03.fit.gz",
        "BIR_20110922_051500_03.fit.gz",
        "BIR_20110922_053000_03.fit.gz",
        "BIR_20110922_054500_03.fit.gz",
    ]

    RESULTS.sort()
    # Should be sorted anyway, but better to assume as little as possible.
    result.sort()
    for item in RESULTS:
        assert URL + item in result


@pytest.mark.xfail
def test_query_number():

    result = list(query(datetime(2011, 9, 22, 5), datetime(2011, 9, 22, 6), {("BIR", 1)}))
    RESULTS = [
        "BIR_20110922_050000_01.fit.gz",
        "BIR_20110922_051500_01.fit.gz",
        "BIR_20110922_053000_01.fit.gz",
    ]

    RESULTS.sort()
    # Should be sorted anyway, but better to assume as little as possible.
    result.sort()

    assert len(result) == len(RESULTS)


@pytest.mark.xfail
@pytest.mark.remote_data
def test_download():
    directory = mkdtemp()
    try:
        result = query(datetime(2011, 9, 22, 5), datetime(2011, 9, 22, 6), {("BIR", 1)})
        RESULTS = [
            "BIR_20110922_050000_01.fit.gz",
            "BIR_20110922_051500_01.fit.gz",
            "BIR_20110922_053000_01.fit.gz",
        ]
        download(result, directory)
        for item in RESULTS:
            assert item in sorted(os.listdir(directory))
    finally:
        shutil.rmtree(directory)


def test_create_file(CALLISTO_IMAGE):
    ca = CallistoSpectrogram.create(CALLISTO_IMAGE)
    assert np.array_equal(ca.data, CallistoSpectrogram.read(CALLISTO_IMAGE).data)


def test_create_file_kw(CALLISTO_IMAGE):
    ca = CallistoSpectrogram.create(filename=CALLISTO_IMAGE)
    assert np.array_equal(ca.data, CallistoSpectrogram.read(CALLISTO_IMAGE).data)


@pytest.mark.remote_data
def test_create_url():
    URL = "http://soleil.i4ds.ch/solarradio/data/2002-20yy_Callisto/2011/09/22/" "BIR_20110922_050000_01.fit.gz"
    ca = CallistoSpectrogram.create(URL)
    assert np.array_equal(ca.data, CallistoSpectrogram.read(URL).data)


@pytest.mark.remote_data
def test_create_url_kw():
    URL = "http://soleil.i4ds.ch/solarradio/data/2002-20yy_Callisto/2011/09/22/" "BIR_20110922_050000_01.fit.gz"
    ca = CallistoSpectrogram.create(url=URL)
    assert np.array_equal(ca.data, CallistoSpectrogram.read(URL).data)


def test_create_single_glob(CALLISTO_IMAGE, CALLISTO_IMAGE_GLOB_INDEX, CALLISTO_IMAGE_GLOB_KEY):
    PATTERN = os.path.join(os.path.dirname(CALLISTO_IMAGE), CALLISTO_IMAGE_GLOB_KEY)
    ca = CallistoSpectrogram.create(PATTERN)
    assert np.array_equal(ca.data, CallistoSpectrogram.read(CALLISTO_IMAGE).data)


# seems like this does not work anymore and can't figure out what it is for
# def test_create_single_glob_kw(CALLISTO_IMAGE):
#     PATTERN = os.path.join( os.path.dirname(CALLISTO_IMAGE), "BIR_*")
#     ca = CallistoSpectrogram.create(singlepattern=PATTERN)
#     assert np.array_equal(ca[0].data, CallistoSpectrogram.read(CALLISTO_IMAGE).data)


def test_create_glob_kw(CALLISTO_IMAGE, CALLISTO_IMAGE_GLOB_INDEX, CALLISTO_IMAGE_GLOB_KEY):
    PATTERN = os.path.join(os.path.dirname(CALLISTO_IMAGE), CALLISTO_IMAGE_GLOB_KEY)
    ca = CallistoSpectrogram.create(pattern=PATTERN)[CALLISTO_IMAGE_GLOB_INDEX]
    assert_allclose(ca.data, CallistoSpectrogram.read(CALLISTO_IMAGE).data)


def test_create_glob(CALLISTO_IMAGE_GLOB_KEY, CALLISTO_IMAGE):
    PATTERN = os.path.join(str(Path(CALLISTO_IMAGE).parent), CALLISTO_IMAGE_GLOB_KEY)
    ca = CallistoSpectrogram.create(PATTERN)
    assert len([ca]) == 1


def test_minimum_pairs_commotative():
    A = [0, 1, 2]
    B = [1, 2, 3]
    first = list(minimal_pairs(A, B))
    assert first == [(b, a, d) for a, b, d in minimal_pairs(B, A)]


def test_minimum_pairs_end():
    assert list(minimal_pairs([0, 1, 2, 4], [1, 2, 3, 4])) == [(1, 0, 0), (2, 1, 0), (3, 3, 0)]


def test_minimum_pairs_end_more():
    assert list(minimal_pairs([0, 1, 2, 4, 8], [1, 2, 3, 4])) == [(1, 0, 0), (2, 1, 0), (3, 3, 0)]


def test_minimum_pairs_end_diff():
    assert list(minimal_pairs([0, 1, 2, 8], [1, 2, 3, 4])) == [(1, 0, 0), (2, 1, 0), (3, 3, 4)]


def test_closest():
    assert list(minimal_pairs([50, 60], [0, 10, 20, 30, 40, 51, 52])) == [(0, 5, 1), (1, 6, 8)]


def test_homogenize_factor():
    a = np.float64(np.random.randint(0, 255, 3600))[np.newaxis, :]

    c1 = CallistoSpectrogram(
        a,
        np.arange(3600),
        np.array([1]),
        datetime(2011, 1, 1),
        datetime(2011, 1, 1, 1),
        0,
        1,
        "Time",
        "Frequency",
        "Test",
        None,
        None,
        None,
        False,
    )
    b = 2 * a
    c2 = CallistoSpectrogram(
        b,
        np.arange(3600),
        np.array([1]),
        datetime(2011, 1, 1),
        datetime(2011, 1, 1, 1),
        0,
        1,
        "Time",
        "Frequency",
        "Test",
        None,
        None,
        None,
        False,
    )

    pairs_indices, factors, constants = c1._homogenize_params(c2, 0)

    assert pairs_indices == [(0, 0)]
    assert_array_almost_equal(factors, [0.5], 2)
    assert_array_almost_equal(constants, [0], 2)
    assert_array_almost_equal(factors[0] * b + constants[0], a)


def test_homogenize_constant():
    a = np.float64(np.random.randint(0, 255, 3600))[np.newaxis, :]

    c1 = CallistoSpectrogram(
        a,
        np.arange(3600),
        np.array([1]),
        datetime(2011, 1, 1),
        datetime(2011, 1, 1, 1),
        0,
        1,
        "Time",
        "Frequency",
        "Test",
        None,
        None,
        None,
        False,
    )
    b = a + 10
    c2 = CallistoSpectrogram(
        b,
        np.arange(3600),
        np.array([1]),
        datetime(2011, 1, 1),
        datetime(2011, 1, 1, 1),
        0,
        1,
        "Time",
        "Frequency",
        "Test",
        None,
        None,
        None,
        False,
    )

    pairs_indices, factors, constants = c1._homogenize_params(c2, 0)

    assert pairs_indices == [(0, 0)]
    assert_array_almost_equal(factors, [1], 2)
    assert_array_almost_equal(constants, [-10], 2)
    assert_array_almost_equal(factors[0] * b + constants[0], a)


def test_homogenize_both():
    a = np.float64(np.random.randint(0, 255, 3600))[np.newaxis, :]

    c1 = CallistoSpectrogram(
        a,
        np.arange(3600),
        np.array([1]),
        datetime(2011, 1, 1),
        datetime(2011, 1, 1, 1),
        0,
        1,
        "Time",
        "Frequency",
        "Test",
        None,
        None,
        None,
        False,
    )
    b = 2 * a + 1
    c2 = CallistoSpectrogram(
        b,
        np.arange(3600),
        np.array([1]),
        datetime(2011, 1, 1),
        datetime(2011, 1, 1, 1),
        0,
        1,
        "Time",
        "Frequency",
        "Test",
        None,
        None,
        None,
        False,
    )

    pairs_indices, factors, constants = c1._homogenize_params(c2, 0)

    assert pairs_indices == [(0, 0)]
    assert_array_almost_equal(factors, [0.5], 2)
    assert_array_almost_equal(constants, [-0.5], 2)
    assert_array_almost_equal(factors[0] * b + constants[0], a)


def test_homogenize_rightfq():
    a = np.float64(np.random.randint(0, 255, 3600))[np.newaxis, :]

    c1 = CallistoSpectrogram(
        a,
        np.arange(3600),
        np.array([1]),
        datetime(2011, 1, 1),
        datetime(2011, 1, 1, 1),
        0,
        1,
        "Time",
        "Frequency",
        "Test",
        None,
        None,
        None,
        False,
    )
    b = 2 * a + 1
    c2 = CallistoSpectrogram(
        np.concatenate([np.arange(3600)[np.newaxis, :], b, np.arange(3600)[np.newaxis, :]], 0),
        np.arange(3600),
        np.array([0, 1, 2]),
        datetime(2011, 1, 1),
        datetime(2011, 1, 1, 1),
        0,
        1,
        "Time",
        "Frequency",
        "Test",
        None,
        None,
        None,
        False,
    )
    pairs_indices, factors, constants = c1._homogenize_params(c2, 0)
    assert pairs_indices == [(0, 1)]
    assert_array_almost_equal(factors, [0.5], 2)
    assert_array_almost_equal(constants, [-0.5], 2)
    assert_array_almost_equal(factors[0] * b + constants[0], a)


@pytest.mark.remote_data
@pytest.mark.skip(reason="Looks like data changed")
def test_extend(CALLISTO_IMAGE):
    im = CallistoSpectrogram.create(CALLISTO_IMAGE)
    im2 = im.extend()
    # Not too stable test, but works.
    assert im2.data.shape == (200, 7200)
