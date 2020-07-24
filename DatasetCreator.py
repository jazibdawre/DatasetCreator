#!/usr/bin/env python3
#================================================================================
'''
    File name: DatasetCreator.py
    Author: Jazib Dawre <jazib980@gmail.com>
    Version: 1.1.0
    Date created: 04/07/2020
    Description: Script for creating a dataset for AI, ML applications
    Python Version: >= 3.6.0 64-bit, <= 3.6.8 64-bit (Tested on 3.6.8 64-bit Windows)
    Optional Repositories: https://github.com/GuillaumeErhard/ImageSetCleaner, https://github.com/tzutalin/labelImg
    License: GPL-3.0 License

    Copyright (C) 2020 Jazib Dawre

    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program.  If not, see <http://www.gnu.org/licenses/>.
'''
#================================================================================
import sys

if sys.version_info[0] != 3:
    err = f"\n Python version {sys.version_info[0]} is not supported"
elif sys.version_info[1] != 6:
    err = f"\n Python version {sys.version_info[0]}.{sys.version_info[1]} is not supported"
elif sys.version_info[2] > 8:
    err = f"\n Python version {sys.version_info[0]}.{sys.version_info[1]}.{sys.version_info[2]} is not supported"
elif not sys.maxsize > 2**32:
    err = f"\n 32-bit Python is not supported"
else:
    err = ""

if err:
    err += "\n Supported python version: 3.6.0 to 3.6.8, 64-bit only"
    print(err)
    sys.exit(0)
#================================================================================
import time, re, os, json, glob, subprocess, shutil, math, random
import imagehash, requests
from PIL import Image
from io import BytesIO
from hashlib import sha1
from selenium import webdriver
from datetime import date, datetime
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.firefox.options import Options
#================================================================================
settings = {    #These are defaults. Overriden by settings.json file
    "no_img":10,
    "target_url": "https://www.google.com/search?safe=off&site=&tbm=isch&source=hp&q={query}&oq={query}&gs_l=img",
    "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:78.0) Gecko/20100101 Firefox/78.0",
    "image_dimension": 416,
    "image_distribution": "70/15/15",
    "driver": "driver/geckodriver.exe",
    "logging": True,
    "download_images": True,
    "remove_duplicate": True,
    "clean_images": False,
    "resize_images": True,
    "mirror_images": True,
    "move_images": True,
    "rename_images": True,
    "label_images": False,
    "stealth": True
}
#================================================================================
def log_run(log):
    if settings["logging"]:
        try:
            if not os.path.exists(os.path.join('logs', 'run')) :
                    os.makedirs(os.path.join('logs', 'run'))

            with open(os.path.join('logs', 'run', 'datasetcreator.log'), "a") as logfile :
                logfile.write(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')}:{log}\n")
        except KeyboardInterrupt:
            raise KeyboardInterrupt()
        except Exception as e:
            print(f"\n [INFO] Run log error{log}\n")

def log_err(log):
    if settings["logging"]:
        try:
            if not os.path.exists(os.path.join('logs', 'err')) :
                    os.makedirs(os.path.join('logs', 'err'))

            with open(os.path.join('logs', 'err', 'datasetcreator.log'), "a") as logfile :
                logfile.write(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')}: {log}")
        except KeyboardInterrupt:
            raise KeyboardInterrupt()
        except Exception as e:
            print(f"\n [INFO] Err log error{log}\n")

def read_settings():
    if os.path.exists("settings.json"):
        global settings 
        settings = dict(json.load(open('settings.json')))
        log_run(" [INFO] Settings read from settings.json")
    else:
        log_run(" [INFO] settings.json not present")

def display_banner():
    print(f"""
                             Dataset Creator v1.1.0
 ==============================================================================
 Github: github.com/jazibdawre/DatasetCreator                   GPL-3.0 License
 Author: Jazib Dawre <jazib980@gmail.com>                   {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
 ==============================================================================

 Current Preferences:
 Base Url :                      {settings["target_url"].split('search')[0]}
 User Agent :                    {(settings["user_agent"][:44] + '..') if len(settings["user_agent"]) > 46 else settings["user_agent"]}
 No of Images :                  {settings["no_img"]}
 Image Size :                    {settings["image_dimension"]}x{settings["image_dimension"]}px
 Stealth Mode :                  {"Yes" if settings["stealth"] else "No"}
 Runtime logging :               {"Yes" if settings["logging"] else "No"}
 Download Images :               {"Yes" if settings["download_images"] else "No"}
 Remove Duplicates :             {"Yes" if settings["remove_duplicate"] else "No"}
 Clean Images :                  {"Yes" if settings["clean_images"] else "No"}
 Resize Images :                 {"Yes" if settings["resize_images"] else "No"}
 Mirror Images :                 {"Yes" if settings["mirror_images"] else "No"}
 Move Images :                   {"Yes" if settings["move_images"] else "No"}
 Rename Images :                 {"Yes" if settings["rename_images"] else "No"}
 Label Images :                  {"Yes" if settings["label_images"] else "No"}

 Preferences can be changed via the settings.json file
 """)
    for i in range(10):
        time.sleep(1)
        print(f" Bot will initialize after {9-i} seconds, Press Ctrl+C to quit", end="\r")
    print(f"\n\n Initializing...")
    log_run(" [INFO] Bot Initializing")

def get_keywords():
    keywords = []
    print("\n Note: each term will be searched separately. Type ... to finish")
    while not keywords or keywords[-1] != "...":
        keywords.append(input(" Search Term: "))
    log_run(" [INFO] Keywords entered")
    return [i for i in keywords if i.strip() and not re.match(r'\. *',i.strip())]

def scroll_to_end(wd, sleep_prd):
    wd.execute_script('window.scrollTo(0, document.body.scrollHeight);')
    time.sleep(sleep_prd)

def fetch_img_urls(query, max_links, wd, sleep_prd=1) :
    err = 0
    try:
        search_url = "https://www.google.com/search?safe=off&site=&tbm=isch&source=hp&q={q}&oq={q}&gs_l=img"

        wd.get(search_url.format(q=query))
        img_thumbnails = wd.find_elements_by_css_selector("img.Q4LuWd")
        log_run(f" [INFO] Thumbnails found: {len(img_thumbnails)}")
        
        img_urls = set()

        while len(img_thumbnails) < max_links:
            scroll_to_end(wd, sleep_prd)
            load_mor_bttn = wd.find_element_by_css_selector('.mye4qd')
            if(load_mor_bttn) :
                wd.execute_script("document.querySelector('.mye4qd').click()")
                log_run(" [INFO] Load more button clicked")
                img_thumbnails = wd.find_elements_by_css_selector("img.Q4LuWd")
            else:
                max_links = len(img_thumbnails)
                break   #End of google page
        log_run(f" [INFO] Thumbnails found: {len(img_thumbnails)}")

        for img in img_thumbnails :
            try :
                img.click()
                time.sleep(sleep_prd*2)
                actual_images = wd.find_elements_by_css_selector('img.n3VNCb')
                for actual_img in actual_images :
                    if(actual_img.get_attribute('src')) :
                        if actual_img.get_attribute('src')[:10] != "data:image":
                            img_urls.add(actual_img.get_attribute('src'))
                            print(f" Extracting image links: {len(img_urls)}/{max_links}", end="\r")
                        if len(img_urls) >= max_links:
                            break
                if len(img_urls) >= max_links:
                    break
            except KeyboardInterrupt:
                raise KeyboardInterrupt()
            except Exception as e:
                    log_err(f"[ERR] {e}\n")
                    err += 1

        log_run(f" [INFO] Image links extracted: {len(img_urls)}")
    except KeyboardInterrupt:
        raise KeyboardInterrupt()
    except Exception as e:
        print(f"\n [ERR] {e}", end="\r")
        log_err(f"[ERR] [MAJOR] {e}\n\n")
    finally:
        if err:
            print(f"\n Links not extracted: {err}", end="\r")
        print("")
        return img_urls

def save_imgs(savepath, urls) :
    err = 0
    try :
        for index, url in enumerate(urls, start=1):
            try:
                img_content = requests.get(url).content
                img_file = BytesIO(img_content)
                img = Image.open(img_file).convert('RGB')
                file_path = os.path.join(savepath,sha1(img_content).hexdigest()[:10] + '.jpg')
                with open(file_path, "wb") as f :
                    img.save(f, 'JPEG', quality=85)
                print(f" Downloading images: {index}/{len(urls)}", end="\r")
            except KeyboardInterrupt:
                raise KeyboardInterrupt()
            except Exception as e:
                    log_err(f"[ERR] {e}\n")
                    err += 1
    except KeyboardInterrupt:
        raise KeyboardInterrupt()
    except Exception as e:
        print(f"\n [ERR] {e}", end="\r")
        log_err(f"[ERR] [MAJOR] {e}\n\n")
    finally:
        log_run(f" [INFO] Images Downloaded")
        if err:
            print(f"\n Images not downloaded: {err}", end="\r")
        print("")

def search_and_download(search_term, driver_path, target_folder, num_imgs) :
    try:
        if not os.path.exists(target_folder) :
            os.makedirs(target_folder)

        options = Options()
        profile = webdriver.FirefoxProfile()

        options.headless = True
        if settings["stealth"]:
            profile.set_preference("general.useragent.override", settings["user_agent"])

        with webdriver.Firefox(executable_path=driver_path, options=options, firefox_profile=profile) as wd :
            log_run(f" [INFO] Opening Browser. Search term: {search_term}")
            urls = fetch_img_urls(search_term, num_imgs, wd, 0.5)
            log_run(f" [INFO] Closing Browser")

        save_imgs(target_folder, urls)
    except KeyboardInterrupt:
        raise KeyboardInterrupt()
    except Exception as e:
        print(f"\n [ERR] {e}")
        log_err(f"[ERR] [MAJOR] {e}\n\n")

def download_images(keywords, target_folder):
    if settings["download_images"]:
        try:
            for keyword in keywords:
                print(f"\n Downloading Images for '{keyword}'")
                search_and_download(keyword, settings["driver"], target_folder, settings["no_img"])    #Considering trash
        except KeyboardInterrupt:
            raise KeyboardInterrupt()
        except Exception as e:
            print(f"\n [ERR] {e}")
            log_err(f"[ERR] [MAJOR] {e}\n\n")
        finally:
            print("")
    else:
        print("\n Image downloading disabled. Skipping...\n")

def alpharemover(image):
    try:
        if image.mode != 'RGBA':
            return image
        canvas = Image.new('RGBA', image.size, (255,255,255,255))
        canvas.paste(image, mask=image)
        return canvas.convert('RGB')
    except KeyboardInterrupt:
        raise KeyboardInterrupt()
    except Exception as e:
        log_err(f"[ERR] {e}\n")

def compute_hash(imagePaths):
    err = 0
    try:
        hashes = {}
        for index, imagePath in enumerate(imagePaths, start=1):
            try:
                # load the input image and compute the hash
                image = alpharemover(Image.open(imagePath))
                h = imagehash.phash(image)
                image.close()
                # grab all image paths with that hash, add the current image
                # path to it, and store the list back in the hashes dictionary
                p = hashes.get(h, [])
                p.append(imagePath)
                hashes[h] = p
                print(f" Computing Hashes: {index}/{len(imagePaths)}", end="\r")
            except KeyboardInterrupt:
                raise KeyboardInterrupt()
            except Exception as e:
                log_err(f"[ERR] {e}\n")
                err += 1
    except KeyboardInterrupt:
        raise KeyboardInterrupt()
    except Exception as e:
        print(f"\n [ERR] {e}")
        log_err(f"[ERR] [MAJOR] {e}\n\n")
    finally:
        log_run(f" [INFO] Computed image hashes")
        if err:
            print(f"\n Images with Hash error: {err}")
        print("")
        return hashes

def delete_duplicates(imagePaths):
    if settings["remove_duplicate"]:
        err = 0
        try:
            hashes = compute_hash(imagePaths)
            index, tot = 1, 0
            for (h, hashedPaths) in hashes.items():
                try:
                    # check to see if there is more than one image with the same hash
                    if len(hashedPaths) > 1:
                        tot = tot + len(hashedPaths[1:])
                        for p in hashedPaths[1:]:       #delete all except one copy
                            os.remove(p)
                            print(f" Deleting Duplicates: {index}/{tot}", end="\r")
                            index = index + 1
                except KeyboardInterrupt:
                    raise KeyboardInterrupt()
                except Exception as e:
                    log_err(f"[ERR] {e}\n")
                    err += 1
            if not tot:
                print(" No duplicates found!", end="\r")
        except KeyboardInterrupt:
            raise KeyboardInterrupt()
        except Exception as e:
            print(f"\n [ERR] {e}", end="\r")
            log_err(f"[ERR] [MAJOR] {e}\n\n")
        finally:
            log_run(f" [INFO] Duplicate images deleted")
            if err:
                print(f"\n Images not deleted: {err}", end="\r")
            print("\n")
    else:
        print(" Duplicate removal disabled. Skipping...\n")

def clean_image(target_folder):
    if settings["clean_images"]:
        try:
            
            print(" Starting Image cleaner GUI.\n Credits to Guillaume Erhard, https://github.com/GuillaumeErhard/ImageSetCleaner")    
            p = subprocess.run(["python", "image_set_cleaner.py", f"--image_dir={os.path.join('..', target_folder)}"], cwd="ImageSetCleaner", stdout = subprocess.PIPE, stderr = subprocess.PIPE, universal_newlines=True)

            if p.returncode != 0:
                if p.stderr.split('\n')[-2] == "AssertionError: No outlier detected in the directory.":
                    print("\n No outliers detected!")
                else:
                    print("\n [WARN] Image cleaner exited with error")
            else:
                print(" Images Cleaned")
            
            if settings["logging"]:
                if not os.path.exists(os.path.join('logs', 'run')) :
                    os.makedirs(os.path.join('logs', 'run'))
                if not os.path.exists(os.path.join('logs', 'err')) :
                    os.makedirs(os.path.join('logs', 'err'))

                with open(os.path.join('logs', 'run', 'imagecleaner.log'), 'a') as run_log, open(os.path.join('logs', 'err', 'imagecleaner.log'), 'a') as err_log:    
                    run_log.write(p.stdout)
                    err_log.write(p.stderr)
        except KeyboardInterrupt:
            raise KeyboardInterrupt()
        except Exception as e:
            print(f"\n [ERR] {e}")
            log_err(f"[ERR] [MAJOR] {e}\n\n")
        finally:
            log_run(f" [INFO] Auto image cleaning done")
    else:
        print(" Auto image cleaning disabled. Skipping...")
    print("\n Waiting for manual review. Press Enter when done...", end="")
    input()
    print("")

def make_square(im, fill_color=(255, 255, 255)):
    x, y = im.size
    size = max(x, y)
    new_im = Image.new('RGB', (size, size), fill_color)
    new_im.paste(im, (int((size - x) / 2), int((size - y) / 2)))
    return new_im

def resize_images(imagePaths):
    if settings["resize_images"]:
        err = 0
        try:
            for index, imagePath in enumerate(imagePaths, start=1):
                try:
                    img = Image.open(imagePath)
                    img = make_square(img)
                    img = img.resize((settings["image_dimension"], settings["image_dimension"]))
                    img.save(imagePath, 'JPEG', quality=85)
                    print(f" Resizing Images: {index}/{len(imagePaths)}", end="\r")
                except KeyboardInterrupt:
                    raise KeyboardInterrupt()
                except Exception as e:
                    log_err(f"[ERR] {e}\n")
                    err += 1
        except KeyboardInterrupt:
            raise KeyboardInterrupt()
        except Exception as e:
            print(f"\n [ERR] {e}", end="\r")
        finally:
            log_run(f" [INFO] Images resized")
            if err:
                print(f"\n Images not resized: {err}", end="\r")
            print("\n")
    else:
        print(" Image resizing disabled. Skipping...\n")

def mirror_images(imagePaths):
    if settings["mirror_images"]:
        err = 0
        try:
            for index, imagePath in enumerate(imagePaths, start=1):
                try:
                    if imagePath[-10:] == "-dbflp.jpg":
                        err += 1       #Already mirrored images
                        continue
                    im = Image.open(imagePath)
                    im2 = im.copy()
                    im.close()
                    #flip image
                    out = im2.transpose(Image.FLIP_LEFT_RIGHT)
                    with open(imagePath[:-4]+"-dbflp.jpg", "wb") as f :
                        out.save(f, 'JPEG', quality=85)
                    print(f" Mirroring Images: {index}/{len(imagePaths)}", end="\r")
                except KeyboardInterrupt:
                    raise KeyboardInterrupt()
                except Exception as e:
                    log_err(f"[ERR] {e}\n")
                    err += 1
        except KeyboardInterrupt:
            raise KeyboardInterrupt()
        except Exception as e:
            print(f"\n [ERR] {e}", end="\r")
        finally:
            log_run(f" [INFO] Images mirrored")
            if err:
                print(f"\n Images not mirrored: {err}", end="\r")
            print("\n")
    else:
        print(" Image mirroring disabled. Skipping...\n")

def move_images(imagePaths, target_folder):
    if settings["move_images"]:
        err = 0
        try:
            files = imagePaths.copy()

            train = os.path.join(target_folder, 'train')
            valid = os.path.join(target_folder, 'valid')
            test = os.path.join(target_folder, 'test')

            valid_val = float(settings["image_distribution"].split('/')[1])/100
            test_val = float(settings["image_distribution"].split('/')[2])/100

            if not os.path.exists(train) :
                os.makedirs(train)
            if not os.path.exists(test) :
                os.makedirs(test)
            if not os.path.exists(valid) :
                os.makedirs(valid)

            #Randomly moving 15% files to valid
            for i in range(math.floor(valid_val * len(imagePaths))) :
                try:
                    rnd_file = random.choice(files)
                    files.remove(rnd_file)  #remove from queue once file is selected. Success/failure handled by exception
                    shutil.move(rnd_file, valid)
                    print(f" Moving images to valid: {i+1}/{math.floor(valid_val * len(imagePaths))}", end="\r")
                except KeyboardInterrupt:
                    raise KeyboardInterrupt()
                except Exception as e:
                    log_err(f"[ERR] {e}\n")
                    err += 1
            print(f"")

            #Randomly moving 15% files to test
            for i in range(math.floor(test_val * len(imagePaths))) :
                try:
                    rnd_file = random.choice(files)
                    files.remove(rnd_file)
                    shutil.move(rnd_file, test)
                    print(f" Moving images to test: {i+1}/{math.floor(test_val * len(imagePaths))}", end="\r")
                except KeyboardInterrupt:
                    raise KeyboardInterrupt()
                except Exception as e:
                    log_err(f"[ERR] {e}\n")
                    err += 1
            print(f"")

            #Moving rest 70% files to train
            for i, rnd_file in enumerate(files) :
                try:
                    shutil.move(rnd_file, train)
                    print(f" Moving images to train: {i+1}/{len(files)}", end="\r")
                except KeyboardInterrupt:
                    raise KeyboardInterrupt()
                except Exception as e:
                    log_err(f"[ERR] {e}\n")
                    err += 1
        except KeyboardInterrupt:
            raise KeyboardInterrupt()
        except Exception as e:
            print(f"\n [ERR] {e}", end="\r")
        finally:
            log_run(f" [INFO] Images moved to {target_folder}+{os.path.join('train','valid','test')}")
            if err:
                print(f"\n Images not moved: {err}", end="\r")
            print("\n")
    else:
        print(" Image moving disabled. Skipping...\n")

def rename_image_set(image_folder, set_name, name):
    err = 0
    try:
        imagePaths = glob.glob(os.path.join(image_folder, "*.jpg"))
        
        for index, imagePath in enumerate(imagePaths, start=1):
            try:
                os.rename(imagePath, os.path.join(os.path.dirname(imagePath), str(time.time())+'_('+str(index)+').jpg'))
            except KeyboardInterrupt:
                raise KeyboardInterrupt()
            except Exception as e:
                log_err(f"[ERR] [in random naming] {e}\n")

        for index, imagePath in enumerate(glob.glob(os.path.join(image_folder, "*.jpg")), start=1):
            try:
                os.rename(imagePath, os.path.join(os.path.dirname(imagePath), name+'_('+str(index)+').jpg'))
                print(f" Renaming Images{set_name}: {index}/{len(imagePaths)}", end="\r")
            except KeyboardInterrupt:
                raise KeyboardInterrupt()
            except Exception as e:
                log_err(f"[ERR] {e}\n")
                err += 1
    except KeyboardInterrupt:
        raise KeyboardInterrupt()
    except Exception as e:
        print(f"\n [ERR] {e}")
        log_err(f"[ERR] [MAJOR] {e}\n\n")
    finally:
        log_run(f" [INFO] Images renamed{set_name}")
        if err:
            print(f"\n Images not Renamed: {err}")
        print("")

def rename_images(imagePaths, target_folder, name):
    if settings["rename_images"]:
        try:
            if not settings["move_images"]:
                rename_image_set(target_folder, "", name)
            else:
                rename_image_set(os.path.join(target_folder, 'valid'), " in valid", name)
                rename_image_set(os.path.join(target_folder, 'test'), " in test", name)
                rename_image_set(os.path.join(target_folder, 'train'), " in train", name)
        except KeyboardInterrupt:
            raise KeyboardInterrupt()
        except Exception as e:
            print(f"\n [ERR] {e}")
            log_err(f"[ERR] [MAJOR] {e}\n\n")
    else:
        print(" Image renaming disabled. Skipping...")
    print("")

def label_image_set(target_folder, name):
    try:
        if name:
            print(f"\n Labelling images{name}")

        p = subprocess.run(["python", "labelImg.py", f"{target_folder}", f"{os.path.join(os.getcwd(), 'labelImg', 'data', 'predefined_classes.txt')}"], cwd="labelImg", stdout = subprocess.PIPE, stderr = subprocess.PIPE, universal_newlines=True)

        if p.returncode != 0:
            if p.stderr.split('\n')[-2] == "ModuleNotFoundError: No module named 'libs.resources'":
                print("\n [WARN] run 'pyrcc5 -o libs/resources.py resources.qrc' in labelImg directory")
            else:
                print(f"\n [WARN] Image labeller exited with error, status code: {p.returncode}")
        else:
            print(" Images labelled")

        if settings["logging"]:
            if not os.path.exists(os.path.join('logs', 'run')) :
                os.makedirs(os.path.join('logs', 'run'))
            if not os.path.exists(os.path.join('logs', 'err')) :
                os.makedirs(os.path.join('logs', 'err'))

            with open(os.path.join('logs', 'run', 'imagelabeller.log'), 'a') as run_log, open(os.path.join('logs', 'err', 'imagelabeller.log'), 'a') as err_log:    
                run_log.write(p.stdout)
                err_log.write(p.stderr)
    except KeyboardInterrupt:
        raise KeyboardInterrupt()
    except Exception as e:
        print(f" [ERR] {e}")
        log_err(f"[ERR] [MAJOR]{name} {e}\n\n")
    finally:
        log_run(f" [INFO] Images labelled{name}")

def label_images(target_folder):
    if settings["label_images"]:
        try:
            print(" Starting Image labeller GUI.\n Credits: Tzutalin,LabelImg-Git code(2015) https://github.com/tzutalin/labelImg")
            if not settings["move_images"]:
                label_image_set(target_folder, "")
            else:
                label_image_set(os.path.join(target_folder, 'valid'), " in valid")
                label_image_set(os.path.join(target_folder, 'test'), " in test")
                label_image_set(os.path.join(target_folder, 'train'), " in train")
        except KeyboardInterrupt:
            raise KeyboardInterrupt()
        except Exception as e:
            print(f"\n [ERR] {e}")
            log_err(f"[ERR] [MAJOR] {e}\n\n")
    else:
        print(" Image labelling disabled. Skipping...")

def main():
    read_settings()
    display_banner()
    keywords = get_keywords()
    target_folder = os.path.join('dataset', keywords[0])
    download_images(keywords,target_folder)
    if glob.glob(os.path.join(target_folder, "*.jpg")):
        delete_duplicates(glob.glob(os.path.join(target_folder, "*.jpg")))
        clean_image(target_folder)
        resize_images(glob.glob(os.path.join(target_folder, "*.jpg")))
        mirror_images(glob.glob(os.path.join(target_folder, "*.jpg")))
        move_images(glob.glob(os.path.join(target_folder, "*.jpg")), target_folder)
        rename_images(glob.glob(os.path.join(target_folder, "*.jpg")), target_folder, keywords[0])
        label_images(os.path.abspath(target_folder))
    else:
        print(" [WARN] No Images to process")
        log_run(" [WARN] No Images to process")

if __name__=='__main__':
    try:
        tic = time.time()
        log_run(f" [INFO] --- Script started at {tic} ---")
        main()
    except json.JSONDecodeError:
        print('\n settings.json is in invalid json format\n -> Check for a comma "," after each field\n -> Make sure strings are enclosed in double quotes "some string"\n -> Verify "image_distribution" key is of string type ex: "70/15/15"')
    except KeyboardInterrupt:
        print("\n\n Keyboard Interrupt Recieved")
        log_run(f" [INFO] Keyboard Interrupt Recieved")
    except Exception as e:
        print(f"\n Uncaught Exception propogated out of main.\n Error is {type(e).__name__}: {e}")
    finally:
        toc = time.time()
        print(f"\n Exiting. Bye")
        print(f" ==============================================================================\n DatasetCreator executed in {int((toc-tic)//60)} minutes and {round((toc-tic)%60, 10)} seconds\n")
        log_run(f" [INFO] --- Script exited at {toc} ---\n")