import os 
import shutil
import tempfile
import time

from pathlib import Path
from PIL import Image as PIL_Image
from glob import glob

from core import BlickUtils as bkt


def run_tests():
    
    print(f"Running BlickUtils version {bkt.version()} tests...\n")

    bkt.get_methods()
    
    
    ############################################################################
    ## Infra Tests 
    ############################################################################

    # Test get_gpu_info and get_device
    gpu_info = bkt.get_gpu_info()
    print(f"Testing get_gpu_info(): {gpu_info}")
    assert gpu_info is not None, "get_gpu_info() should return a value"
    
    device = bkt.get_device()
    print(f"Testing get_device(): {device}")
    assert device is not None, "get_device() should return a device"

    mem = bkt.get_mem()
    print(f"Testing get_mem(): {mem}")
    assert mem is not None, "get_mem() should return memory information"

    cpu = bkt.get_cpu()
    print(f"Testing get_cpu(): {cpu}")
    assert cpu is not None, "get_cpu() should return CPU information"


    ############################################################################
    ## Image Tests
    ############################################################################
    
    # Test get_urls
    urls = bkt.get_urls('bla bla bla https://google.com blabla http://test.de/test.png')
    print(f'Testing get_urls(): {urls}')
    assert isinstance(urls, list), "get_urls() should return a list"
    assert len(urls) == 2, "get_urls() should find 2 URLs"
    assert 'https://google.com' in urls, "Should find https://google.com"
    assert 'http://test.de/test.png' in urls, "Should find http://test.de/test.png"

    # Test get_pil with invalid input
    invalid_pil = bkt.get_pil('jkjshkadf')
    print(f'Testing get_pil(invalid): {invalid_pil}')
    assert invalid_pil is None, "get_pil() should return None for invalid input"
    
    # Test get_pil with URL
    url_pil = bkt.get_pil('https://blicktek.com/assets/images/blick-logo-final-square-160x160.png')
    print(f'Testing get_pil(url): {url_pil.size}')
    assert url_pil is not None, "get_pil() should load image from URL"
    assert isinstance(url_pil.size, tuple), "PIL Image should have a size tuple"
    assert len(url_pil.size) == 2, "Image size should be (width, height)"
    
    # Test get_pil with base64
    base64_sample = 'data:image/gif;base64,R0lGODlhAQABAAAAACH5BAEKAAEALAAAAAABAAEAAAICTAEAOw==' 
    b64_im1 = bkt.get_pil(base64_sample)
    print(f'Testing get_pil(base64): {b64_im1.size}')
    assert b64_im1 is not None, "get_pil() should decode base64 image"
    assert b64_im1.size == (1, 1), "Sample GIF should be 1x1 pixels"
    
    # Test get_base64
    base64_generated = bkt.get_base64(b64_im1)
    print(f'Testing get_base64(): {base64_generated[:50]}...')
    assert isinstance(base64_generated, str), "get_base64() should return a string"
    assert base64_generated.startswith('data:image'), "Base64 should have proper data URI prefix"
            
    # Test round-trip: base64 -> PIL -> base64
    im2 = bkt.get_pil(base64_generated)
    print(f'Testing get_pil(generated base64): {im2.size}')
    assert im2 is not None, "get_pil() should decode generated base64"
    assert im2.size == b64_im1.size, "Round-trip should preserve image dimensions"

    print("Testing has_same_resolution")
    a = PIL_Image.new("RGB", (100, 100), (0, 0, 0))
    b = PIL_Image.new("RGB", (100, 100), (255, 255, 255))
    c = PIL_Image.new("RGB", (101, 100), (0, 0, 0))
    d = PIL_Image.new("RGB", (200, 200), (0, 0, 0))

    assert bkt.has_same_resolution(a, b) is True
    assert bkt.has_same_resolution(a, c, th_px=1) is True
    assert bkt.has_same_resolution(a, c, th_px=0) is False

    print("Testing get_same_resolution")
    a_resized = bkt.get_same_resolution(a, d)
    assert a_resized.size == d.size
    assert a_resized.mode == a.mode


    # get_median
    print("Testing get_median")
    im_med = PIL_Image.new("L", (5, 5), color=100)
    im_med.putpixel((2, 2), 0)  # pepper noise
    out_med = bkt.get_median(im_med, radius=1)  # 3x3 kernel
    assert out_med.getpixel((2, 2)) == 100

    # get_gray
    print("Testing get_gray")
    im_rgb = PIL_Image.new("RGB", (4, 4), (255, 0, 0))
    im_gray = bkt.get_gray(im_rgb)
    assert im_gray.mode == "L"
    # Expected around 0.299*255 = 76
    assert im_gray.getpixel((0, 0)) == int(0.299 * 255)

    # posterize
    print("Testing posterize")
    w, h = 256, 1
    grad = PIL_Image.new("L", (w, h))
    for x in range(w):
        grad.putpixel((x, 0), x)
    post = bkt.posterize(grad, qtd_bits=2)
    vals = set(post.getdata())
    assert vals.issubset({0, 64, 128, 192})
    assert len(vals) == 4

    # diff_im - no difference
    print("Testing diff_im (no difference)")
    a0 = PIL_Image.new("L", (10, 10), color=100)
    b0 = PIL_Image.new("L", (10, 10), color=100)
    qtd0, diff0 = bkt.diff_im(a0, b0, diff_th=0)
    assert qtd0 == 0
    assert diff0.getextrema() == (0, 0)

    # diff_im - directional difference + resize
    print("Testing diff_im (directional and resize)")
    a1 = PIL_Image.new("L", (5, 5), color=100)   # will be resized to b1
    b1 = PIL_Image.new("L", (6, 5), color=100)

    higher_coords = [(1, 1), (2, 1), (3, 1), (1, 2), (2, 2), (3, 2)]
    for xy in higher_coords:
        b1.putpixel(xy, 120)  # b - a = +20

    lower_coords = [(0, 0), (4, 4), (5, 4)]
    for xy in lower_coords:
        b1.putpixel(xy, 0)  # b - a = -100 (should NOT count)

    qtd1, diff1 = bkt.diff_im(a1, b1, diff_th=10)
    assert qtd1 == len(higher_coords)

    hist = diff1.histogram()
    white = hist[255]
    black = hist[0]
    assert white == len(higher_coords)
    assert black == (b1.size[0] * b1.size[1] - white)    
    
    # Autocrop
    print("Testing autocrop - crops uniform borders")
    base = PIL_Image.new("RGB", (100, 60), (255, 255, 255))       # white background
    content = PIL_Image.new("RGB", (40, 30), (0, 0, 0))           # black content
    base.paste(content, (10, 5))                                  # content at (10,5)
    out = bkt.autocrop(base, smooth=False)
    assert out.size == (40, 30)
    assert out.getpixel((0, 0)) == (0, 0, 0)

    # Autocrop - no cropping when uniform background is not detected
    uni = PIL_Image.new("RGB", (50, 50), (200, 200, 200))
    out2 = bkt.autocrop(uni)
    assert out2.size == (50, 50)

    print("Testing autocrop - strength threshold")
    weak = PIL_Image.new("RGB", (40, 30), (128, 128, 128))        # gray background
    weak_rect = PIL_Image.new("RGB", (10, 10), (125, 125, 125))   # very close to bg
    weak.paste(weak_rect, (5, 5))
    out_high = bkt.autocrop(weak, strength=15)                    # high threshold -> likely no crop
    assert out_high.size == (40, 30)
    out_low = bkt.autocrop(weak, strength=0)                      # low threshold -> crop to content
    assert out_low.size == (10, 10)
    
    
    ############################################################################
    ## Filesystem Tests
    ############################################################################
    
    # Test get_files
    files = bkt.get_files()
    print(f'Testing get_files(): {files}')
    assert isinstance(files, list), "get_files() should return a list"
    
    # To-Do: Add tests for get_parent, get_parents, get_filename
    
    # Test get_dirs
    dirs = bkt.get_dirs()
    print(f'Testing get_dirs(): {dirs}')
    assert isinstance(dirs, list), "get_dirs() should return a list"
    
    # Test dir2df
    df = bkt.dir2df('.')
    print(f'Testing dir2df(): {df.shape}')
    assert df is not None, "dir2df() should return a dataframe"
    assert len(df) > 0, "Dataframe should have rows"
    
    # Add test for split_df
    
    # Test execute_cmd
    cmd = "ls -lah"
    res_code, res_out = bkt.execute_cmd(cmd)
    print('Testing execute_cmd():')
    print(f'  Command: {cmd}')
    print(f'  Exit Code: {res_code}')
    print(f'  Output: {res_out.strip().splitlines()[0]}...')
    assert res_code == 0, "ls command should succeed"
    assert isinstance(res_out, str), "Command output should be a string"
    assert len(res_out) > 0, "Command output should not be empty"
    
    # Test fn_has_same_size
    print("Testing fn_has_same_size...")
    
    def _write_random_file(path: str, size_bytes: int) -> None:
        with open(path, "wb") as f:
            f.write(os.urandom(size_bytes))
            
    with tempfile.TemporaryDirectory() as td:
        a = os.path.join(td, "a.bin")
        b = os.path.join(td, "b.bin")
        _write_random_file(a, 4096)
        _write_random_file(b, 4096 + 500) 

        assert bkt.fn_has_same_size(a, a) is True

        _write_random_file(a, 4096)
        assert bkt.fn_has_same_size(a, b) is False
        
        _write_random_file(a, 4096)
        assert bkt.fn_has_same_size(a, None) is False
        
        _write_random_file(a, 4096)
        assert bkt.fn_has_same_size(b, "123") is False
        
    # Test get_hash
    hash_val = bkt.get_hash('Hello World!')
    print(f'Testing get_hash(str): {hash_val}')
    assert isinstance(hash_val, str), "get_hash() should return a string"
    assert len(hash_val) > 0, "Hash should not be empty"
    
    
    ############################################################################
    ## Zip File Tests
    ############################################################################

    print('Testing zip')

    # Create temporary directory for testing
    temp_dir = Path(tempfile.mkdtemp())
        
    try:
        # Test 1: Zip a string
        print("Test 1: Zip a string")
        text = "Hello World! " * 100
        compressed = bkt.zip(text)
        print(f"Original length: {len(text)}")
        print(f"Compressed length: {len(compressed)}")
        print(f"Compressed (first 50 chars): {compressed[:50]}...\n")
        assert isinstance(compressed, str), "Compressed string should be string"
        assert len(compressed) < len(text), "Compressed should be smaller than original"
        
        # Test 2: Zip a single file
        print("Test 2: Zip a single file")
        test_file = temp_dir / "test.txt"
        test_file.write_text("This is a test file.")
        zip_path = bkt.zip(str(test_file))
        print(f"Created zip: {zip_path}\n")
        assert os.path.exists(zip_path), "Zip file should be created"
        assert zip_path.endswith('.zip'), "Output should be a zip file"
        
        # Test 3: Zip a single file with custom target
        print("Test 3: Zip a single file with custom target")
        zip_path = bkt.zip(str(test_file), target="custom_name")
        print(f"Created zip: {zip_path}\n")
        assert os.path.exists(zip_path), "Custom zip file should be created"
        assert "custom_name" in zip_path, "Custom name should be in zip path"
        
        # Test 4: Zip files matching a mask
        print("Test 4: Zip files matching a mask")
        for i in range(3):
            (temp_dir / f"video{i}.mp4").write_text(f"Video {i}")
        
        zip_path = bkt.zip(str(temp_dir / "*.mp4"))
        print(f"Created zip: {zip_path}\n")
        assert os.path.exists(zip_path), "Wildcard zip file should be created"
        
        # Test 5: Zip a directory
        print("Test 5: Zip a directory")
        test_dir = temp_dir / "my_folder"
        test_dir.mkdir()
        (test_dir / "file1.txt").write_text("File 1")
        (test_dir / "file2.txt").write_text("File 2")
        
        zip_path = bkt.zip(str(test_dir))
        print(f"Created zip: {zip_path}\n")
        assert os.path.exists(zip_path), "Directory zip file should be created"
        
        # Test 6: Unzip a compressed string
        print("Test 6: Unzip a compressed string")
        original_text = "Hello World! " * 100
        compressed = bkt.zip(original_text)
        decompressed = bkt.unzip(compressed)
        print(f"Original == Decompressed: {original_text == decompressed}")
        print(f"Decompressed (first 50 chars): {decompressed[:50]}...\n")
        assert original_text == decompressed, "Decompressed text should match original"
        
        # Test 7: Unzip a file (auto-create directory)
        print("Test 7: Unzip a file (auto-create directory)")
        test_dir = temp_dir / "test_folder"
        test_dir.mkdir(exist_ok=True)
        (test_dir / "file1.txt").write_text("Content 1")
        (test_dir / "file2.txt").write_text("Content 2")
        (test_dir / "file3.txt").write_text("Content 3")
        
        zip_file = bkt.zip(str(test_dir), target=str(temp_dir / "archive.zip"))
        print(f"  Created zip: {zip_file}")
        
        extract_dir = bkt.unzip(zip_file)
        print(f"  Extracted to: {extract_dir}")
        assert os.path.exists(extract_dir), "Extract directory should be created"
        
        extracted_files = bkt.get_files(os.path.join(extract_dir, 'test_folder'))
        extracted_files = sorted([Path(f).name for f in extracted_files])
        original_files = sorted([f.name for f in test_dir.glob('*') if f.is_file()])
        print(f"    Original files: {original_files}")
        print(f"    Extracted files: {extracted_files}")
        assert original_files == extracted_files, "File names should match after extraction"
        
        all_contents_match = True
        for file_name in original_files:
            original_content = (test_dir / file_name).read_text()
            extracted_content = Path((os.path.join(extract_dir, 'test_folder', file_name))).read_text()
            if original_content != extracted_content:
                print(f"  Content mismatch in {file_name}")
                all_contents_match = False
            else:
                print(f"  {file_name}: content matches")
        
        assert all_contents_match, "All file contents should match after extraction"
        print(f"    All contents match: {all_contents_match}\n")
        
        # Test 8: Unzip to custom directory
        print("Test 8: Unzip to custom directory")
        extract_dir = bkt.unzip(zip_file, target_dir=str(os.path.join(temp_dir,"custom_extract")))
        extract_dir = os.path.join(extract_dir, 'test_folder')
        read_files = bkt.get_files(extract_dir)
        print(f"  Extracted to: {extract_dir} - Total files: {len(read_files)}")
        assert len(read_files) == 3, "Should have 3 extracted files"
        
        extracted_files = sorted([f.name for f in Path(extract_dir).glob('*') if f.is_file()])
        print(f"  Extracted files: {extracted_files}")
        assert original_files == extracted_files, "File names should match in custom directory"
        
        all_contents_match = True
        for file_name in original_files:
            original_content = (test_dir / file_name).read_text()
            extracted_content = Path((os.path.join(extract_dir, file_name))).read_text()
            if original_content != extracted_content:
                print(f"  Content mismatch in {file_name}")
                all_contents_match = False
            else:
                print(f"  {file_name}: content matches")
        
        assert all_contents_match, "All file contents should match in custom directory"
        print(f"All contents match: {all_contents_match}\n")
        
        print("All tests completed successfully!")
                
    finally:
        # Cleanup
        shutil.rmtree(temp_dir, ignore_errors=True)
        for f in glob("*.zip"):
            try:
                os.remove(f)
            except:
                pass    

    ############################################################################
    ## Multi-Threaded Tests
    ############################################################################

    # Test function 1: Single argument
    def square(x):
        time.sleep(0.1)
        return x * x
    
    # Test function 2: Multiple arguments
    def multiply(x, y):
        time.sleep(0.1)
        return x, y, x * y
    
    def test_cmd(cmd):
        time.sleep(0.05)
        return bkt.execute_cmd(cmd)
    
    # Test 1: Single argument function with simple list
    print("Generating multhreaded test data...")
    N = 1000
    cands = list(range(N))
    print("  Test 1: Single argument function with simple list")
    results = bkt.run_parallel(square, cands, threads="16x")
    print(f"Results: {len(results)}")
    assert results == [x**2 for x in range(N)], "Parallel square should return correct values"
    
    # Test 2: Multiple argument function with list of lists
    N=1000
    print("  Test 2: Multiple argument function with list of lists")
    pairs = [[n, n+1] for n in range(N)]
    exp_results = [(n, n+1, n*(n+1)) for n in range(N)]
    results = bkt.run_parallel(multiply, pairs, "max")
    print(f"Results: {len(results)}")
    assert results == exp_results, "Parallel multiply should return correct values"
    
    # Test 3: Using 8x threads
    print("  Test 3: Using 8x threads")
    results = bkt.run_parallel(square, range(100), threads="8x")
    print(f"Results: {len(results)} items")
    assert len(results) == 100, "Should have 100 results"
    assert results[10] == 100, "square(10) should be 100"
    assert results[99] == 9801, "square(99) should be 9801"
    
    # Test 4: Command execution in parallel
    print("  Test 4: Command execution in parallel")
    commands = ["echo Hello", "echo World", "echo Test"]
    results = bkt.run_parallel(test_cmd, commands, threads=3)
    assert len(results) == 3, "Should have 3 results"
    for i, (code, output) in enumerate(results):
        print(f"Command {i}: exit_code={code}, output={output.strip()}")
        assert code == 0, f"Command {i} should succeed"
        assert isinstance(output, str), f"Command {i} output should be a string"
            

if __name__ == "__main__":    
    run_tests()