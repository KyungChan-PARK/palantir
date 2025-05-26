def test_main_importable():
    import main
    assert hasattr(main, "app") 