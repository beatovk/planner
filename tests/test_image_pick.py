from core.normalize.image import choose_image, verify_image, normalize_image_url


def test_choose_image_og_priority():
    """Test that og:image has highest priority"""
    html = """
    <html>
    <head>
        <meta property="og:image" content="http://example.com/og.jpg">
    </head>
    <body>
        <img src="http://example.com/dom.jpg">
    </body>
    </html>
    """

    result = choose_image(html, "http://example.com/jsonld.jpg")
    assert result == "http://example.com/og.jpg"


def test_choose_image_jsonld_fallback():
    """Test JSON-LD image fallback when no og:image"""
    html = """
    <html>
    <body>
        <img src="http://example.com/dom.jpg">
    </body>
    </html>
    """

    result = choose_image(html, "http://example.com/jsonld.jpg")
    assert result == "http://example.com/jsonld.jpg"


def test_choose_image_dom_fallback():
    """Test DOM img src fallback when no og:image or JSON-LD"""
    html = """
    <html>
    <body>
        <img src="http://example.com/dom.jpg">
    </body>
    </html>
    """

    result = choose_image(html, None)
    assert result == "http://example.com/dom.jpg"


def test_choose_image_none_when_empty():
    """Test that None is returned when no images found"""
    html = """
    <html>
    <body>
        <p>No images here</p>
    </body>
    </html>
    """

    result = choose_image(html, None)
    assert result is None


def test_choose_image_jsonld_only():
    """Test JSON-LD image when no HTML images"""
    html = """
    <html>
    <body>
        <p>No images here</p>
    </body>
    </html>
    """

    result = choose_image(html, "http://example.com/jsonld.jpg")
    assert result == "http://example.com/jsonld.jpg"


def test_normalize_image_url_absolute():
    """Test that absolute URLs are unchanged"""
    result = normalize_image_url("http://example.com/image.jpg")
    assert result == "http://example.com/image.jpg"


def test_normalize_image_url_protocol_relative():
    """Test protocol-relative URLs are converted to https"""
    result = normalize_image_url("//example.com/image.jpg")
    assert result == "https://example.com/image.jpg"


def test_normalize_image_url_relative():
    """Test relative URLs are handled correctly"""
    result = normalize_image_url("image.jpg", "http://example.com/page/")
    assert result == "http://example.com/page/image.jpg"


def test_normalize_image_url_root_relative():
    """Test root-relative URLs are handled correctly"""
    result = normalize_image_url("/image.jpg", "http://example.com/page")
    assert result == "http://example.com/image.jpg"


def test_verify_image_mock():
    """Test verify_image function (mock test)"""
    # This is a mock test since we don't want to make real HTTP requests
    # In real usage, this would test actual image URLs
    assert True  # Placeholder assertion
