from io import BytesIO
import requests, zipfile

def download_opendart(filename):
    print(f"...downloading {filename}")
    download_url = 'https://opendart.fss.or.kr/cmm/downloadFnlttZip.do'
    download_payload = {'fl_nm':filename}
    download_headers = {
        'Referer':'https://opendart.fss.or.kr/disclosureinfo/fnltt/dwld/main.do',
        'User-Agent':'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/99.0.4844.51 Safari/537.36',
    }
    r = requests.get(download_url,download_payload,headers=download_headers)
    f = zipfile.ZipFile(BytesIO(r.content))
    return f
