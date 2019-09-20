# 2019 카카오 블라인드 테스트 2차 구현

FIFO + collective method를 사용하였습니다.
먼저 FIFO로 처음 포인트를 잡고, 그 뒤로 start - end 사이에서 일어나는 요청이 들어오면 한꺼번에 처리하는 알고리즘입니다.
최적화 되어 있지 않고, 2020 블라인드 테스트를 준비하면서 구현해봤습니다.


![execution.gif](execution.gif)
