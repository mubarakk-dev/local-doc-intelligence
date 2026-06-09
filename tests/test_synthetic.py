from docintel.synthetic import generate_synthetic_dataset


def test_generate_synthetic_dataset_can_write_degraded_images(tmp_path) -> None:
    records = generate_synthetic_dataset(
        samples_dir=tmp_path / "samples",
        ground_truth_path=tmp_path / "ground_truth.json",
        image_dir=tmp_path / "images",
        degraded_image_dir=tmp_path / "degraded",
    )

    assert len(records) == 8
    assert len(list((tmp_path / "samples").glob("*.txt"))) == 8
    assert len(list((tmp_path / "images").glob("*.png"))) == 8
    assert len(list((tmp_path / "degraded").glob("*.png"))) == 8
    assert (tmp_path / "ground_truth.json").exists()