import argparse
import requests
import os
from time import sleep
import concurrent.futures

def parse_args():
    parser = argparse.ArgumentParser(description='Clone from the https://anonymous.4open.science')
    parser.add_argument('--dir', type=str, default='master',
                        help='save dir')
    parser.add_argument('--url', type=str,
                        help='target anonymous github link eg., https://anonymous.4open.science/r/840c8c57-3c32-451e-bf12-0e20be300389/')
    parser.add_argument('--max-conns', type=int, default=128,
                        help='max connections number')
    return parser.parse_args()

def dict_parse(dic, pre=None):
    pre = pre[:] if pre else []
    if isinstance(dic, dict):
        for key, value in dic.items():
            if isinstance(value, dict):
                for d in dict_parse(value, pre + [key]):
                    yield d
            else:
                yield pre + [key, value]
    else:
        yield pre + [dic]

def req_url(dl_file, max_retry=5):
    url = dl_file[0]
    save_path = dl_file[1]
    save_dir = '/'.join(save_path.split('/')[:-1])
    if not os.path.exists(save_dir) and save_dir:
        try:
            os.makedirs(save_dir)
        except OSError:
            pass
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/15.2 Safari/605.1.15"
    }
    for i in range(max_retry):
        try:
            r = requests.get(url, headers=headers)
            with open(save_path, "wb") as f:
                f.write(r.content)
            return
        except Exception as e:
            print('file request exception (retry {}): {} - {}'.format(i, e, save_path))
            sleep(0.4)


if __name__ == '__main__':
    args = parse_args()
    assert args.url, '\nPlese specifipy your target anonymous github link, \n e.g:    '\
            +'python download.py --target https://anonymous.4open.science/r/840c8c57-3c32-451e-bf12-0e20be300389/'
    
    url = args.url
    name = url.split('/')[-2]
    max_conns = args.max_conns

    print("[*] cloning project:" + name)
    
    list_url = "https://anonymous.4open.science/api/repo/"+ name +"/files/"
    headers = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/15.2 Safari/605.1.15"
    }
    resp = requests.get(url=list_url, headers=headers)
    file_list = resp.json()

    print("[*] downloading files:")
    
    dl_url = "https://anonymous.4open.science/api/repo/"+ name +"/file/"
    files = []
    out = []
    for file in dict_parse(file_list):
        file_path = os.path.join(*file[-len(file):-2]) # * operator to unpack the arguments out of a list
        save_path = os.path.join(args.dir, file_path)
        file_url = dl_url + file_path
        files.append((file_url, save_path))
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=max_conns) as executor:
        future_to_url = (executor.submit(req_url, dl_file) for dl_file in files)
        for future in concurrent.futures.as_completed(future_to_url):
            try:
                data = future.result()
            except Exception as exc:
                data = str(type(exc))
            finally:
                out.append(data)

                print(str(len(out)),end="\r")
    
    print("[*] files saved to:" + args.dir)