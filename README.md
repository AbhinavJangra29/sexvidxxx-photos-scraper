# sexvidxxx-photos-scraper
`pip install --upgrade selenium urllib3`

only for research purposes(nsfw text 2 image models)
uses selenium and chrome driver to scrape high quality images from https://www.sexvid.xxx/photos/ and https://www.pornpics.com/{topic}/ , currently tested on linux containers on runpod

to setup chrome driver on linux container:

```python
apt-get update && \
    apt-get install -y gnupg wget curl unzip --no-install-recommends && \
    wget -q -O - https://dl-ssl.google.com/linux/linux_signing_key.pub | apt-key add - && \
    echo "deb http://dl.google.com/linux/chrome/deb/ stable main" >> /etc/apt/sources.list.d/google.list && \
    apt-get update -y && \
    apt-get install -y google-chrome-stable && \
    CHROMEVER=$(google-chrome --product-version | grep -o "[^.].[^.].[^.]") && \
    DRIVERVER=$(curl -s "https://chromedriver.storage.googleapis.com/LATEST_RELEASE_$CHROMEVER") && \
    wget -q --continue -P /chromedriver "http://chromedriver.storage.googleapis.com/$DRIVERVER/chromedriver_linux64.zip" && \
    unzip /chromedriver/chromedriver -d /chromedriver

```
