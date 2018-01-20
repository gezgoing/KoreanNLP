
from konlpy.tag import Twitter
from gensim.models import word2vec
import json
import re


# json 포맷으로 구성된 한 라인을 입력받아 body 필드 값만을 반환하는 함수
# 기본적인 전처리로, '다.'로 끝나는 마지막 문장까지만 추출한다.
def get_body(json_line):
    body = json_line['body']
    if "다." in body:
        rindex = body.rfind("다.")              # 텍스트 맨 뒤에서 '다.'의 인덱스 찾음
        if rindex > 0:
            cut_body = body[0:rindex + 2]       # 텍스트 잘라내기
            return cut_body
    return ""


# 입력받은 텍스트 한 라인에 대해 전처리를 수행하는 함수
def preprocess(text):
    # 라인이 '다.'로 끝나는 문장이 아닐 경우 학습하지 않음
    if "다." not in text:
        return ""

    # 마지막 '다.'까지만 사용하고 나머지는 버림
    da_index = text.rfind("다.")
    text = text[0:da_index+2]

    # 특정 특수문자 제거
    target_list = ["\t", "…", "·", "●", "○", "◎", "△", "▲", "◇", "■", "□", "☎", "☏", "※", "▶", "▷",
                   "ℓ", "→", "↓", "↑", "┌", "┬", "┐", "├", "┤", "┼", "─", "│", "└", "┴", "┘"]
    for target in target_list:
        text = text.replace(target, " ")        # 해당 특수문자를 white space로 교체

    # 정규표현식을 이용한 전처리
    gija_str1 = r"[^ ]*[ ]?기자[ ]?[a-zA-Z0-9]*@[a-zA-Z0-9]*\.co[^ ]*"   # ex. "홍길동 기자 hong@abcd.co.kr"
    gija_str2 = r"[^ ]*[ ]?기자[ ]?[a-zA-Z0-9]*@"                        # ex. "홍길동 기자 hong@"

    # 패턴 컴파일
    patt1 = re.compile(gija_str1)
    patt2 = re.compile(gija_str2)

    # 해당 패턴이 text에 존재할 경우 제거함
    text = re.sub(patt1, "", text)
    text = re.sub(patt2, "", text)

    strip_text = text.strip()                   # 텍스트 전후 공백 제거
    return strip_text


# 전처리된 텍스트(뉴스 body)를 입력받아 형태소 분석을 수행하는 함수
# 기본형으로 전환된 형태소들을 white space로 구분하여 하나의 string으로 만든다
def get_pos(body):
    twitter = Twitter()
    results = []
    lines = body.split("\n")

    for line in lines:
        preproc_line = preprocess(line)         # 텍스트 한 라인의 전처리
        if len(preproc_line) > 0:               # 전처리 후 유효한 텍스트일 경우에만 형태소 분석
            malist = twitter.pos(preproc_line, norm=True, stem=True)    # 단어의 기본형 사용
            r = []                              # 기본형 문장을 저장할 리스트

            for word in malist:
                # 어미/조사/구두점 등은 대상에서 제외
                if not word[1] in ["Josa", "Eomi", "Punctuation"]:
                    r.append(word[0])

            rl = (" ".join(r)).strip()          # 리스트를 string으로 변환
            results.append(rl)                  # results 리스트에 삽입
    return results                              # string들의 리스트를 반환


# 텍스트 한 라인을 파일에 append 모드로 저장하기
def append_text_to_file(text, file_name):
    with open(file_name, "a", encoding="utf-8") as f:
        f.write(text)
        f.close()


# 로드된 json 리스트를 입력받아 각 json의 body만 추출하여 plain text로 반환하는 함수
def gen_plain_text(json_lines, wakati_file_name):
    for line in json_lines:
        body = get_body(line)                   # json 포맷의 한 라인에서 body 필드값 추출
        if len(body) > 0:                       # 내용물이 존재하면
            posed_list = get_pos(body)          # 형태소 분석 및 기본형으로 구성된 문장 생성
            for posed in posed_list:
                append_text_to_file(posed, wakati_file_name)    # 형태소 분석된  텍스트 라인을 파일로 저장하기(append)


# plain text를 학습한 word2vec 모델을 생성하는 함수
def get_w2v_model(wakati_file):
    data = word2vec.LineSentence(wakati_file)
    model = word2vec.Word2Vec(data, size=200, window=10, hs=1, min_count=2, sg=1)
    return model


# 메인 필드
if __name__ == "__main__":

    # 데이터 로드. json 포맷의 라인들로 이뤄진 리스트를 load_data에 저장함
    with open("../data/digitaltimes.json", encoding="utf-8") as fload:
        loaded_data = [json.loads(line) for line in fload]

    # 형태소 분석된 텍스트를 저장할 파일 이름
    wakati_file = "digitaltimes.wakati"

    # 로드된 데이터를 형태소 분석하고 plain text를 만들어 저장하는 함수
    gen_plain_text(loaded_data, wakati_file)

    # plain text로 word2vec 모델 학습시키기
    digit_w2v_model = get_w2v_model(wakati_file)

    # 학습된 모델 저장
    digit_w2v_model.save("../model/digitaltimes.model")

    print("\n>> [INFO] Generating word2vec model finished!")
