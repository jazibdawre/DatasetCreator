# DatasetCreator
Python script for creating a dataset for AI, ML applications

## Repositories
ImageSetCleaner by GuillaumeErhard at https://github.com/GuillaumeErhard/ImageSetCleaner, licensed under GPL-3.0 license is used for semi-supervised image cleaning. For fine tuning the predictions, read the readme on the above link.

The entire repository is cloned in this repository under ImageSetCleaner/ .

## Requirements

- Python >= 3.6.0, <=3.6.8  64-bit only
- Libraries: Pillow, selenium, requests, imagehash, tensorflow, numpy, matplotlib, PyQt5, six, scikit_learn

Note: the libraries can be installed by
```
pip install -r requirements.txt
```

## Usage

Set you preferences in settings.json file, then run the script as

```
python DatasetCreator.py
```
On the prompt for search term, enter the word/sentence as you would in a search bar.
```
 Note: each term will be searched separately. Type ... to finish
 Search Term: cat eating grass
 Search Term:                               <- Lines with only spaces/empty lines will be ignored
 Search Term: .                             <- Lines with only full stops are ignored
 Search Term: ..                            <- Ignored
 Search Term: why is a cat eating grass
 Search Term: ...                           <- This signifies end of input, bot will start to fetch images
```
## How it Works

1. The bot first accesses google.com and extracts the selenium object for each image thumbnail
2. Then the url of each image is extracted from the thumbnail and downloaded to dataset/search_term/
4. Hashes are calculated for each image using phash algorithm and the duplicates are deleted
5. ImageSetCleaner is used to filter out bad images from the dataset
6. The images are then converted to a square dimension while maintaining the aspect ratio
7. The square images are resized,mirrored and distributed into train/valid/test folders in the dataset/search_term/ directory
8. The images are renamed sequentially starting from 1 to n separately for each train, valid and test folder

## Settings
The settings can be changed via the settings.json file
```
"no_img"                The number of images to download (approximately)

"target_url"            This is the base url

"stealth"               When enabled the bot will identify as the user-agent defined in the settings dictionary

"user_agent"            We pretend to be this in stealth mode. Use any valid UA string you like

"image_dimension"       Dimension of images in dataset if "resize_images" is True

"image_distribution"    Ratio of images in train/valid/test set. ex: "70/15/15"

"driver"                Path to the webdriver for the browser. ex: driver/geckodriver.exe for firefox

"logging"               Enable logging of events and errors in log/run and log/err

"download_images"       Weather to download images via browser.

"remove_duplicate"      Delete duplicate images by phash algorithm

"clean_images"          Use semi-supervised deep learning tool to filter out bad images

"resize_images"         resize images to image_dimension*image_dimension pixels

"mirror_images"         mirror every image in the dataset

"move_images"           distribute images in train/valid/test folder based on image_distribution value

"rename_images"         rename images as 'first search term_(image_no)'.
```

## Possible changes
1. If you require images to be less than 300px, you can use Beautiful Soup instead of selenium for a much much faster execution. You need to change the code in 'fetch_img_urls' function.
2. Incase of pre-downloaded images, place the folder containing the images in the 'dataset' folder and enter the folder name as the first search term. Set 'download_images' setting to false

Released under the GPL-3.0 license