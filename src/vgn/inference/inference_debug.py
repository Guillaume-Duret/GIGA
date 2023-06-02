import pathlib
import numpy as np
from PIL import Image
import spatialmath as sm
from vgn.utils import visual
from vgn.inference.inference_class import GIGAInference, INTRINSICS



if __name__ == "__main__":
    # Get data
    try:
        from centergrasp_fmm.zed2 import ZED2Camera
        camera = ZED2Camera()
        rgb_uint8_np, depth_np, _ = camera.get_image()
    except:
        print("Zed Camera not found, using saved data instead")
        img_path = pathlib.Path(__file__).parent
        rgb_uint8_np = np.array(Image.open(img_path / "rgb.png"))
        depth_uint16 = np.array(Image.open(img_path / "depth.png"))
        depth_np = depth_uint16.astype(np.float32) / 1000.0

    wTcam = sm.SE3(
        np.array(
            [
                [-0.00288795, -0.84104389, 0.54095919, 0.46337467],
                [-0.99974617, -0.00965905, -0.02035441, -0.07190939],
                [0.0223441, -0.54088066, -0.84080251, 1.06529043],
                [0.0, 0.0, 0.0, 1.0],
            ]
        ),
        check=False,
    )
    wTtask = sm.SE3.Trans([0.7, -0.24, 0.655])
    camTtask = wTcam.inv() * wTtask
    model_dir = pathlib.Path(__file__).parents[3] / "data/models"

    # Initialize
    camTtask = wTcam.inv() * wTtask
    giga_inference = GIGAInference(model_dir, camera_intrinsic=INTRINSICS)
    
    # Do inference
    grasps, scores, inference_time, tsdf_pc, pred_mesh = giga_inference.predict(
        depth_np, camTtask.A, reconstruction=True
    )
    best_grasp = sm.SE3.Rt(R=grasps[0].pose.rotation.as_matrix(), t=grasps[0].pose.translation)
    wTgrasp = wTtask * best_grasp

    # Visualize
    grasp_mesh_list = [visual.grasp2mesh(g, s) for g, s in zip(grasps, scores)]
    grasp_mesh = grasp_mesh_list[0] if len(grasp_mesh_list) > 0 else None
    giga_inference.visualize(grasp_mesh, wTcam, wTtask, tsdf_pc, rgb_uint8_np, depth_np, pred_mesh)
