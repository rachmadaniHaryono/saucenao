"""test saucenow module."""
from tempfile import NamedTemporaryFile
import json
import logging
import os

from PIL import Image
import vcr

from saucenao.saucenao import SauceNao


logger = logging.getLogger()


@vcr.use_cassette('vcr_cassettes/test_check_image_html.yaml')
def test_check_image_html():
    test_dir = os.path.dirname(__file__)
    with open(os.path.join(test_dir, 'test_data', 'test_check_image_html.json')) as f:
        exp_res = json.load(f)
    pic_path = os.path.join(test_dir, 'test_data', 'test_check_image_html.jpg')
    img = Image.new('RGB', (150, 150), color = 'red')
    img.save(pic_path)
    sn = SauceNao('')
    res = sn.check_image(pic_path, SauceNao.API_HTML_TYPE)
    assert json.loads(res) == exp_res
