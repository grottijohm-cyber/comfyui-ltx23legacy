import base64
import io
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from PIL import Image

import worker


def png_bytes():
    output = io.BytesIO()
    Image.new("RGB", (4, 4), "red").save(output, format="PNG")
    return output.getvalue()


class WorkflowTests(unittest.TestCase):
    def test_bundled_workflow_is_valid_image_to_video_api_graph(self):
        workflow = worker.load_workflow(Path("api-workflow.json"))
        self.assertEqual(workflow["350"]["class_type"], "LoadImage")
        self.assertEqual(workflow["449"]["class_type"], "VHS_VideoCombine")
        load_images = [
            node for node in workflow.values() if node["class_type"] == "LoadImage"
        ]
        self.assertEqual(len(load_images), 1)

    def test_decodes_raw_base64_and_data_uri(self):
        data = png_bytes()
        encoded = base64.b64encode(data).decode("ascii")
        self.assertEqual(worker._decode_image_input(encoded), data)
        self.assertEqual(
            worker._decode_image_input(f"data:image/png;base64,{encoded}"), data
        )

    def test_rejects_non_image_bytes(self):
        with self.assertRaises(worker.WorkerError):
            worker._validate_image(b"not an image")

    def test_extracts_videohelpersuite_gif_descriptor(self):
        entry = {
            "outputs": {
                "449": {
                    "gifs": [
                        {
                            "filename": "LTX2_3_00001-audio.mp4",
                            "subfolder": "",
                            "type": "output",
                        }
                    ]
                }
            }
        }
        descriptors = worker.get_output_descriptors(entry)
        self.assertEqual(descriptors[0]["filename"], "LTX2_3_00001-audio.mp4")

    @patch.object(worker, "publish_output")
    @patch.object(worker, "_safe_output_path")
    @patch.object(worker, "get_output_descriptors")
    @patch.object(worker, "wait_for_history")
    @patch.object(worker, "queue_workflow")
    @patch.object(worker, "upload_input_image")
    @patch.object(worker, "wait_for_comfyui")
    def test_job_only_needs_image(
        self,
        wait_for_comfyui,
        upload_input_image,
        queue_workflow,
        wait_for_history,
        get_output_descriptors,
        safe_output_path,
        publish_output,
    ):
        upload_input_image.return_value = "job.png"
        queue_workflow.return_value = "prompt-1"
        wait_for_history.return_value = {"outputs": {}}
        get_output_descriptors.return_value = [{"filename": "result.mp4"}]
        safe_output_path.return_value = Path("/tmp/result.mp4")
        publish_output.return_value = {
            "filename": "result.mp4",
            "type": "url",
            "url": "https://example.com/result.mp4",
            "mime_type": "video/mp4",
        }

        with tempfile.NamedTemporaryFile("w", suffix=".json") as workflow_file:
            json.dump(
                {
                    "350": {
                        "inputs": {"image": "placeholder.png"},
                        "class_type": "LoadImage",
                    },
                    "449": {
                        "inputs": {"images": ["350", 0]},
                        "class_type": "VHS_VideoCombine",
                    },
                },
                workflow_file,
            )
            workflow_file.flush()
            with patch.object(worker, "WORKFLOW_PATH", Path(workflow_file.name)):
                result = worker.handle_job(
                    {
                        "id": "job-1",
                        "input": {
                            "image": "data:image/png;base64,"
                            + base64.b64encode(png_bytes()).decode("ascii")
                        },
                    }
                )

        self.assertEqual(result["status"], "success")
        queued = queue_workflow.call_args.args[0]
        self.assertEqual(queued["350"]["inputs"]["image"], "job.png")

    def test_rejects_extra_inputs(self):
        result = worker.handle_job({"input": {"image": "abc", "prompt": "no"}})
        self.assertIn("Only input.image", result["error"])


if __name__ == "__main__":
    unittest.main()
