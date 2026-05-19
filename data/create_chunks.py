"""
chunk data 생성
영상 길이 2분, encoding별 chunk 개수 -> HQ(45), MQ(30), LQ(15) 

< 구현 필요한 기능 >
1. 영상 길이 및 인코딩별 청크 수로 분할
2. 청크 당 재생시간 계산하여 start/end time 명세 꼴로 반환
3. dcit 생성하여 JSON 꼴로 저장

"""
import json 

def main(): 
    movies = {
        str(movie_id): create_chunks(movie_id)
        for movie_id in range(1,10)
    }

    with open("data/chunks.json", "w") as file :
        json.dump(movies, file, indent=2)

# 시간을 명세에서 요구한 꼴의 문자열로 변환
def ms_to_time_str(total_ms: int) -> str:
    h = total_ms // 3600000
    m = (total_ms % 3600000) // 60000
    s = (total_ms% 60000) // 1000
    ms = total_ms % 1000
    return f"{h:02d}:{m:02d}:{s:02d}:{ms:03d}"

# 파라미터로 받은 영화를 위에서 정해진 chunk_number 개수로 분할
# 이후 movie_3_qaulities 딕셔너리에 영화별로 모든 인코딩 정리
def create_chunks(movie_id: int) -> dict:
    movie_3_qaulities = {}
    encoding_quality = ["HQ", "MQ", "LQ"]
    for quality in encoding_quality:
        if quality == "HQ":
            count = 45
        elif quality == "MQ":
            count = 30
        else:
            count = 15
        
        length_per_chunk = 120000 // count
        movie_chunks = []

        current_ms = 0
        for i in range(count):
            next_ms = current_ms + length_per_chunk
            
            movie_chunks.append({
                "chunk_index": i,
                "start_time": ms_to_time_str(current_ms),
                "end_time": ms_to_time_str(next_ms),
            })
            current_ms = next_ms
        movie_3_qaulities[quality] = movie_chunks
    return movie_3_qaulities

if __name__ == "__main__":
    main()

