"""
Main utilities class for blick_utils
"""
import base64
import os
from io import BytesIO


class BlickUtils:
    """
    A collection of static utility methods for Blick Technologies
    """

    @staticmethod
    def is_empty(obj):
        """
        Returns True if the object is considered empty (None, empty string, empty list, etc.)
        """
        
        if obj is None:
            return True

        if str(obj).strip() == '':
            return True
        
        import re
        if re.sub(r'\s', '', str(obj)) == '':
            return True

        if isinstance(obj, list) and len(obj) == 0:
            return True

        try:
            if len(obj) == 0:
                return True
        except:
            pass

        return False

        
    @staticmethod
    def get_gpu_info():
        """
        Returns GPU information including device count, names, and memory
        
        Returns:
            dict: Dictionary containing GPU information or error message
        """
        try:
            import torch
        except ImportError:
            torch = None

        try:
            import GPUtil
        except ImportError:
            GPUtil = None

        gpu_info = {
            "gpu_available": False,
            "gpu_count": 0,
            "gpu_devices": None,
            "cuda_available": False,
            "cuda_count": 0,
            "cuda_devices": None,
        }   

        if GPUtil is not None:
            try:
                gpus = GPUtil.getGPUs()
                
                if not gpus:
                    return gpu_info
                
                gpu_info["gpu_available"] = True
                gpu_info["gpu_count"] = len(gpus)
                gpu_info["gpu_devices"] = []
                
                for gpu in gpus:
                    gpu_info["gpu_devices"].append({
                        "id": gpu.id,
                        "name": gpu.name,
                        "total_memory_gb": round(gpu.memoryTotal / 1024, 2),
                        "used_memory_gb": round(gpu.memoryUsed / 1024, 2),
                        "free_memory_gb": round(gpu.memoryFree / 1024, 2),
                        "memory_util_percent": round(gpu.memoryUtil * 100, 1),
                        "gpu_util_percent": round(gpu.load * 100, 1),
                        "temperature_c": gpu.temperature,
                        "uuid": gpu.uuid
                    })
                
                return gpu_info
            except Exception as e:
                print(f"Warning: install GPUtil for better GPU info: pip install GPUtil")
        else:
            print(f"Warning: install GPUtil for better GPU info: pip install GPUtil")

        if torch is None:
            print(f"Warning: install torch with CUDA for correct device detection: pip3 install torch torchvision --index-url https://download.pytorch.org/whl/cu126     - Further info :https://pytorch.org/get-started/locally/")
            return gpu_info
        
        if torch.cuda.is_available():
            gpu_info["cuda_available"] = True
            gpu_info["cuda_count"] = torch.cuda.device_count()
            gpu_info["cuda_devices"] = []
        
            for i in range(torch.cuda.device_count()):
                device_props = torch.cuda.get_device_properties(i)
                gpu_info["cuda_devices"].append({
                    "id": i,
                    "name": device_props.name,
                    "total_memory_gb": round(device_props.total_memory / 1024**3, 2),
                    "compute_capability": f"{device_props.major}.{device_props.minor}"
                })
        
        return gpu_info
    
    
    @staticmethod
    def get_gpu(id=0):
        """
        Returns torch device (GPU if available, otherwise CPU)
        
        Args:
            id: The ID of the GPU to use (default is 0)

        Returns:
            torch.device: CUDA device if available, otherwise CPU device
        """
        try:
            import torch
        except:
            print(f"Warning: install torch with CUDA for correct device detection: pip3 install torch torchvision --index-url https://download.pytorch.org/whl/cu126     - Further info :https://pytorch.org/get-started/locally/")
            return "cpu"

        return torch.device(f"cuda:{id}" if torch.cuda.is_available() else "cpu")


    @staticmethod
    def get_cuda(id=0):
        """Alias for get_gpu to maintain compatibility"""
        return BlickUtils.get_gpu(id)


    @staticmethod
    def get_device(id=0):
        """Alias for get_gpu to maintain compatibility"""
        return BlickUtils.get_gpu(id)

    
    @staticmethod
    def get_pil(whatever, flatten=True):
        """
        Get a Pillow Image from various sources
        
        Args:
            whatever: Input which can be a URL, file path, numpy array, or base64 string
            flatten: Whether to convert image to RGB (3 channels)
            
        Returns:
            PIL.Image.Image: Pillow Image object
            
        Raises:
            ValueError: If no valid input is provided or multiple inputs are provided
            ImportError: If required libraries are not installed
        """

        # Other imports are done on demand to avoid unnecessary dependencies
        from PIL import Image as PIL_Image

        if BlickUtils.is_empty(whatever):
            return None
        
        pil_im = None

        if isinstance(whatever, PIL_Image.Image):
            pil_im = whatever

        elif str(whatever).startswith("http://") or str(whatever).startswith("https://"):
            # Load from URL
            import requests
            try:
                response = requests.get(str(whatever).strip())
                #response.raise_for_status()
                pil_im = PIL_Image.open(BytesIO(response.content))
            except Exception as e:
                print(f"Warning: Unable to get image from URL: {e}")
                return None

        elif os.path.isfile(whatever):
            # Load from file path
            pil_im = PIL_Image.open(whatever) 
        
        elif isinstance(whatever, (str)):
            # Assume base64 string
            try:
                base64_str = str(whatever).strip()
                # Remove data URI prefix if present
                if "," in base64_str:
                    base64_str = base64_str.split(",")[1]
                image_data = base64.b64decode(base64_str)
                pil_im = PIL_Image.open(BytesIO(image_data))
            except Exception as e:
                print(f"Warning: Unable to get image from Base64: {e}")
                return None
        
        else:
            # Assume numpy array
            array = whatever

            import numpy as np
            return PIL_Image.fromarray(whatever)

        if pil_im is not None:        
            if flatten:
                pil_im = pil_im.convert("RGB")

        return pil_im
    
    

    @staticmethod
    def get_files(directory='.', ext='*', recursive=False):
        """
        Retorns a list of files in a directory with specified extensions
        
        Args:
            directory: directory path to search
            ext: file extension(s) to filter by. Options:
                - '*' or None: all files
                - '.mp4': specific extension
                - ['.mp4', '.avi', '.mov']: extensions list
            recursive: if True, searches subdirectories recursively
        Returns:
            List[str]: full paths of matching files
        """
        from pathlib import Path
        
        if BlickUtils.is_empty(directory):
            return []
        
        path = Path(directory)
        
        if not path.exists():
            return []
        
        if not path.is_dir():
            return []
        
        files = []
        
        # Normalize the extensions input
        if ext is None or str(ext).strip() == '*':
            extensions = ['*']
        elif isinstance(ext, str):
            # Removes the "." from extension if missing
            extensions = [str(ext).strip() if str(ext).strip().startswith('.') else f'.{str(ext).strip()}']
        elif isinstance(ext, list):
            # Extensions list
            extensions = [str(e).strip() if str(e).strip().startswith('.') else f'.{str(e).strip()}' for e in ext]
        else:
            extensions = ['*']
        
        # Busca arquivos
        for extension in extensions:
            try:
                if extension == '*':
                    pattern = '*'
                else:
                    pattern = f'*{extension}'
                
                if recursive:
                    # Recursively searches in all subdirectories
                    for file in path.rglob(pattern):
                        if file.is_file():
                            files.append(str(file.absolute()))
                else:
                    # Searches only in the specified directory
                    for file in path.glob(pattern):
                        if file.is_file():
                            files.append(str(file.absolute()))
            except PermissionError:
                print(f"No permission to access '{directory}'")
                continue
            except Exception as e:
                continue
            
        # Remove duplicates
        files = list(set(files))
        files.sort()  # Ordena alfabeticamente
        
        return files
            

    @staticmethod
    def get_dirs(directory='.', recursive = False):
        """
        Get all directories in a directory
        
        Args:
            dir: Directory path to search
            recursive: Whether to search subdirectories recursively
            
        Returns:
            List[str]: List of directory paths
        """
        from pathlib import Path
        
        if BlickUtils.is_empty(directory):
            return []
        
        dir_path = Path(directory)
        
        if not dir_path.exists():
            return []
        
        if not dir_path.is_dir():
            return []
        
        dirs = []
        
        if recursive:
            pattern = "**/*"
        else:
            pattern = "*"
        
        for item in dir_path.glob(pattern):
            # Skip .. and . entries
            if item.name in ('.', '..'):
                continue
            
            try:
                if item.is_dir():
                    dirs.append(str(item))
            except PermissionError:
                print(f"No permission to access '{item}'")
                continue
            except Exception as e:
                continue
        
        return sorted(dirs)
    
        
    @staticmethod 
    def dir2df(directory='.', ext='*', recursive=False):
        """
        Returns a pandas DataFrame with files in 3 columns: file_path, file_name, dir
        
        Args:
            directory: Directory path to search
            ext: File extension(s) to filter by. Options:
                - '*' or None: all files
                - '.mp4': specific extension
                - ['.mp4', '.avi', '.mov']: extensions list
            recursive: Whether to search subdirectories recursively
            
        Returns:
            pd.DataFrame: DataFrame with file paths and names
        """
        import pandas as pd
        
        files = BlickUtils.get_files(directory=directory, ext=ext, recursive=recursive)
        
        if not files:
            return pd.DataFrame(columns=['fullpath', 'filename', 'dir'])
        
        data = {
            'fullpath': files,
            'filename': [os.path.basename(f) for f in files],
            'dir': [str(os.path.dirname(f)).split(os.path.sep)[-1] for f in files]            
        }
        
        df = pd.DataFrame(data)
        
        return df
        
        

if __name__ == "__main__":    
    bkt = BlickUtils

    print('get_gpu_info(): ', bkt.get_gpu_info())
    print('get_device(): ', bkt.get_device())
    print('get_pil(invalid): ', bkt.get_pil('jkjshkadf'))
    print('get_pil(url): ', bkt.get_pil('http://archive.net.im/images/TV.png').size)
    print('get_pil(base64): ', bkt.get_pil('data:image/gif;base64,R0lGODlhAQABAAAAACH5BAEKAAEALAAAAAABAAEAAAICTAEAOw==').size)
    print('get_files(): ', bkt.get_files())
    print('get_dirs(): ', bkt.get_dirs())
    print('dir2df(): \n', bkt.dir2df('.'))
