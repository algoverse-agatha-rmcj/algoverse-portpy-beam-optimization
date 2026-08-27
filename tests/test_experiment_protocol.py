import json
import tempfile
import unittest
from pathlib import Path

from scripts.experiment_protocol import (
    CUSTOM_EXPERIMENT_ID,
    DOWNSAMPLE_BEAMLET_FACTOR,
    DOWNSAMPLE_VOXEL_FACTORS,
    EXPERIMENT_ID,
    PRIMARY_GENERATIONS,
    PRIMARY_K,
    PRIMARY_MUTATION_RATE,
    PRIMARY_POPULATION,
    PRIMARY_SEED,
    build_run_manifest,
    batch_manifest,
    cache_payload,
    downsample_dimensions,
    fingerprint,
    primary_config_mismatches,
    primary_scientific_config,
    scientific_config,
    validated_cache_entries,
)


class PrimaryProtocolTests(unittest.TestCase):
    def test_primary_protocol_is_the_existing_seed_zero_cohort(self):
        config = primary_scientific_config()
        self.assertEqual(config["beam_count"], PRIMARY_K)
        self.assertEqual(config["population"], PRIMARY_POPULATION)
        self.assertEqual(config["generations"], PRIMARY_GENERATIONS)
        self.assertEqual(config["mutation_rate"], PRIMARY_MUTATION_RATE)
        self.assertEqual(config["seed"], PRIMARY_SEED)
        self.assertEqual(config["downsample_voxel_factors"], [6, 6, 1])
        self.assertEqual(config["downsample_beamlet_factor"], 4)

    def test_downsampling_recipe_has_one_source_of_truth(self):
        voxels, width, height = downsample_dimensions((3.0, 3.0, 2.5), 2.5, 5.0)
        self.assertEqual(voxels, [18.0, 18.0, 2.5])
        self.assertEqual(width, 10.0)
        self.assertEqual(height, 20.0)
        self.assertEqual(DOWNSAMPLE_VOXEL_FACTORS, (6, 6, 1))
        self.assertEqual(DOWNSAMPLE_BEAMLET_FACTOR, 4)

    def test_legacy_result_can_be_checked_without_receiving_new_optimizer_data(self):
        result = {
            "k": 7,
            "pop": 20,
            "gens": 40,
            "mutation_rate": 0.15,
            "seed": 0,
        }
        self.assertEqual(primary_config_mismatches(result), [])
        result["seed"] = 1
        self.assertIn("seed: expected 0, found 1", primary_config_mismatches(result))

    def test_non_primary_seed_is_labeled_as_a_separate_experiment(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            patient = "Lung_Patient_21"
            patient_dir = root / "data" / patient
            patient_dir.mkdir(parents=True)
            (patient_dir / "PlannerBeams.json").write_text(json.dumps({"IDs": [0, 3]}))
            config = scientific_config(
                k=7,
                population=20,
                generations=40,
                mutation_rate=0.15,
                seed=1,
                downsampled=True,
            )
            manifest = build_run_manifest(
                patient=patient,
                candidate_pool=[0, 3, 6],
                angle_map={0: 0.0, 3: 15.0, 6: 30.0},
                clinician_beams=[0, 3],
                config=config,
                repo_root=root,
                data_dir=root / "data",
            )
            self.assertEqual(manifest["experiment_id"], CUSTOM_EXPERIMENT_ID)
            self.assertNotEqual(manifest["experiment_id"], EXPERIMENT_ID)

    def test_batch_manifest_predeclares_exact_patient_list(self):
        with tempfile.TemporaryDirectory() as directory:
            patients = ["Lung_Patient_21", "Lung_Patient_22"]
            manifest = batch_manifest(
                batch_id="extension-test",
                patients=patients,
                repo_root=directory,
            )
            self.assertEqual(manifest["patients_predeclared"], patients)
            self.assertEqual(manifest["scientific_config"], primary_scientific_config())
            self.assertEqual(
                {patient: row["status"] for patient, row in manifest["patients"].items()},
                {patient: "pending" for patient in patients},
            )


class CacheIdentityTests(unittest.TestCase):
    def test_matching_cache_identity_round_trips(self):
        identity = {"patient": "Lung_Patient_21", "config": "abc"}
        entries = [{"beams": [0, 3, 6], "score": 12.5}]
        payload = cache_payload(identity, entries)
        self.assertEqual(validated_cache_entries(payload, identity), entries)

    def test_mismatched_cache_is_rejected(self):
        payload = cache_payload(
            {"patient": "Lung_Patient_21", "config": "abc"},
            [],
        )
        with self.assertRaisesRegex(RuntimeError, "protocol mismatch"):
            validated_cache_entries(
                payload,
                {"patient": "Lung_Patient_21", "config": "different"},
            )

    def test_legacy_unidentified_cache_is_rejected(self):
        with self.assertRaisesRegex(RuntimeError, "no verifiable protocol identity"):
            validated_cache_entries([{"beams": [0, 3, 6], "score": 12.5}], {})

    def test_fingerprint_is_stable_and_configuration_sensitive(self):
        config = primary_scientific_config()
        self.assertEqual(fingerprint(config), fingerprint(dict(reversed(list(config.items())))))
        changed = dict(config)
        changed["seed"] = 1
        self.assertNotEqual(fingerprint(config), fingerprint(changed))


if __name__ == "__main__":
    unittest.main()
