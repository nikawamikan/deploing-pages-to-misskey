# コンソールからのデプロイ用スクリプト
import requests
import json
from argparse import ArgumentParser
import os
from dotenv import load_dotenv
import shutil






load_dotenv()

# 環境変数から取得
TOKEN = os.getenv("TOKEN")
BASE_URL = os.getenv("BASE_URL")

# 環境変数がない場合は異常終了
if TOKEN is None:
    print("環境変数TOKENが設定されていません")
    exit(1)

if BASE_URL is None:
    print("環境変数BASE_URLが設定されていません")
    exit(1)

pages_dir = "pages/"

if not os.path.isdir(pages_dir):
    os.mkdir(pages_dir)


remove_keys_list = [
    "id",
    "createdAt",
    "updatedAt",
    "likedCount",
    "userId",
    "user",
    "isPublic",
    "eyeCatchingImage",
    "eyeCatchingImageId",
    "attachedFiles",
    "isLiked",
]

def remove_keys(data: dict, append_keys_list: list = []):
    """dictから不要なキーを削除する"""

    for key in remove_keys_list + append_keys_list:
        if key in data:
            del data[key]

# indexからページIDを取得する関数
def get_page_id(index: int, pages: dict):
    """indexからページIDを取得する"""

    # indexが範囲外の場合は異常終了
    if index < 0 or index >= len(pages):
        print(f"indexが範囲外です: {index}")
        exit(1)

    return list(pages.keys())[index]


def load_pages():
    """pages.jsonを読み込む"""
    try:
        with open(f"{pages_dir}pages.json", mode="r", encoding="utf-8") as f:
            pages = json.load(f)
    except FileNotFoundError as e:
        print(f"ファイルが見つかりません: {e}")
        exit(1)

    return pages

def show_pages(pages: dict):
    """pagesを一覧表示する"""
    for  i, (page_id, page) in enumerate(pages.items()):
        print(f"{i+1}: \n  {page_id}: {page['title']}\n  summary: {page['summary']}")


# pages.jsonを読み込み一覧表示を行い、ページIDを返す関数
def select_page(pages: dict):
    """pagesを一覧表示し、ページIDを返す"""

    # pagesを一覧表示
    show_pages(pages)

    # 入力を受け付ける
    index = input("ページを選択してください: ")

    # 入力が数字以外の場合は再度入力を受け付ける
    while not index.isdigit():
        index = input("数字を入力してください: ")

    # indexからページIDを取得
    page_id = get_page_id(int(index)-1, pages)

    return page_id


# script.isとcontent.jsonを再取得する関数
def reload():
    """script.isとcontent.jsonを削除して、再度取得する"""
    endpoint=f"{BASE_URL}i/pages"
    response = requests.post(endpoint, data={"i": TOKEN})

    # jsonをdictに変換
    response_dict = json.loads(response.text)

    # response_dictが空の場合は異常終了
    if len(response_dict) == 0:
        print("ページがありません")
        exit(1)

    # pages一覧表示用のdictを作成
    pages = {}

    for page_obj in response_dict:
        # dataディレクトリ内にページIDのディレクトリを作成
        page_id = page_obj["id"]
        page_dir = f"{pages_dir}{page_id}/"
        if not os.path.isdir(page_dir):
            os.mkdir(page_dir)

        # script.isを書き出し
        with open(f"{page_dir}script.is", mode="w") as f:
            f.write(page_obj["script"])

        # pages一覧表示用のdictに追加
        pages[page_id] = {
            "title": page_obj["title"],
            "summary": page_obj["summary"],
        }

        # 不要なキーを削除
        remove_keys(page_obj, ["script"])

        # jsonを書き出し
        with open(f"{page_dir}content.json", mode="w") as f:
            f.write(json.dumps(page_obj, indent=4, ensure_ascii=False))
    
    # pages一覧表示用のdictを書き出し
    with open(f"{pages_dir}pages.json", mode="w") as f:
        f.write(json.dumps(pages, indent=4, ensure_ascii=False))


def deploy(page_id: str):
    """content.jsonにscript.isを結合して、デプロイする"""
    page_dir = f"{pages_dir}{page_id}/"

    try:
        # script.isを読み込み
        with open(f"{page_dir}script.is", mode="r") as f:
            script = f.read()
        # content.jsonを読み込み
        with open(f"{page_dir}content.json", mode="r", encoding="utf-8") as f:
            json_data = json.load(f)
    except FileNotFoundError as e:
        print(f"ファイルが見つかりません: {e}")
        exit(1)

    # content.jsonにscript.isを結合
    json_data["script"] = script

    # json_dataから不要なキーを削除
    remove_keys(json_data)

    # json_strと現在のページを比較する
    endpoint=f"{BASE_URL}pages/show"
    response = requests.post(endpoint, data={"pageId": page_id})

    # responseが200以外の場合は異常終了
    if response.status_code != 200:
        print(f"ステータスコードが200以外です: {response.status_code}\n{response.text}")
        exit(1)

    # responseをdictに変換
    response_dict = json.loads(response.text)

    # response_dictから不要なキーを削除
    remove_keys(response_dict)

    # json_data と response_dict を比較
    if json_data == response_dict:
        print("変更がありません")
        # 変更がない場合は終了
        return

    # tokenを追加
    json_data["i"] = TOKEN
    # pageIdを追加
    json_data["pageId"] = page_id

    # jsonをstrに変換
    json_data = json.dumps(json_data)
    
    # デプロイ
    endpoint=f"{BASE_URL}pages/update"
    response = requests.post(endpoint, data=json_data)

    # レスポンスコードが20４以外の場合は異常終了
    if response.status_code != 204:
        print(f"ステータスコードが204以外です: {response.status_code}\n{response.text}")
        exit(1)

    print("デプロイ完了")


def main():
    parser = ArgumentParser(
        description="mkkey.netのデプロイスクリプト"
    )

    parser.add_argument("--reload", action="store_true", help="script.isとcontent.jsonを再取得")
    parser.add_argument("--deploy", action="store_true", help="script.isをデプロイ")
    parser.add_argument("--show", action="store_true", help="ページIDを表示")
    parser.add_argument("--page_id", help="ページIDを指定")
    args = parser.parse_args()

    if args.reload:
        reload()
    elif args.deploy:
        if args.page_id is None:
            # ページIDがない場合は一覧表示
            page_id = select_page(load_pages())
        else:
            page_id = args.page_id
        deploy(page_id)
    elif args.show:
        # ページIDを表示
        page_id = select_page(load_pages())
        # vscodeで開く
        os.system(f"code {pages_dir}{page_id}/script.is")
    else:
        # 引数がない場合はヘルプを表示
        parser.print_help()

if __name__ == "__main__":
    main()


