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

    for page_obj in response_dict:
        # dataディレクトリ内にページIDのディレクトリを作成
        page_id = page_obj["id"]
        page_dir = f"{pages_dir}{page_id}/"
        if not os.path.isdir(page_dir):
            os.mkdir(page_dir)

        # script.isを書き出し
        with open(f"{page_dir}script.is", mode="w") as f:
            f.write(page_obj["script"])

        # jsonを書き出し
        with open(f"{page_dir}content.json", mode="w") as f:
            f.write(json.dumps(page_obj, indent=4, ensure_ascii=False))


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
    del json_data["id"]
    del json_data["createdAt"]
    del json_data["updatedAt"]
    del json_data["likedCount"]
    del json_data["userId"]
    del json_data["user"]
    del json_data["isPublic"]
    del json_data["eyeCatchingImage"]
    del json_data["eyeCatchingImageId"]
    del json_data["attachedFiles"]
    del json_data["isLiked"]

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
    del response_dict["id"]
    del response_dict["createdAt"]
    del response_dict["updatedAt"]
    del response_dict["likedCount"]
    del response_dict["userId"]
    del response_dict["user"]
    del response_dict["isPublic"]
    del response_dict["eyeCatchingImage"]
    del response_dict["eyeCatchingImageId"]
    del response_dict["attachedFiles"]

    # ファイル書き出し
    with open(f"{page_dir}test.json", mode="w") as f:
        f.write(json.dumps(json_data, indent=4, ensure_ascii=False))

    with open(f"{page_dir}test2.json", mode="w") as f:
        f.write(json.dumps(response_dict, indent=4, ensure_ascii=False))

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
    parser.add_argument("--page_id", help="ページIDを指定")
    args = parser.parse_args()

    if args.reload:
        reload()
    elif args.deploy:
        if args.page_id is None:
            print("ページIDを指定してください")
            exit(1)
        deploy(args.page_id)
    else:
        # 引数がない場合はヘルプを表示
        parser.print_help()

if __name__ == "__main__":
    main()


