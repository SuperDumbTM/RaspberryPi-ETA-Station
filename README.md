# RaspberryPi-ETA-Station

![output](https://user-images.githubusercontent.com/71750702/177256250-56625f1c-f7bb-487d-9ce6-c91fcf683998.jpg)
<br>Waveshare 3.7" (epd3in7) 預覽

# Dependencies & Library
- Python (≥3.10)
  - [Pillow](https://pypi.org/project/Pillow/)
  - [Requests](https://pypi.org/project/requests/)

#### Waveshare e-paper display
- [Waveshare](https://www.waveshare.com/wiki/Main_Page#Display-e-Paper) 自行參考相應型號之頁面
  - BCM2835
  - WiringPi (官方已停止更新，[WiringPi fork](https://github.com/WiringPi/WiringPi))
  - [RPi.GPIO](https://pypi.org/project/RPi.GPIO/)
  - [spidev](https://pypi.org/project/spidev/)
  
# Usage
設定：`python3 main.py -c`

執行：`python3 main.py <flags>`
