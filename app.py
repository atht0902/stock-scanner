SELECT 
    stock_name, 
    current_price, 
    change_rate, 
    market_cap
FROM 
    stocks_table
WHERE 
    market_cap_rank <= 100        -- '우량주' 기준 (예: 시총 상위 100개)
    AND change_rate > 0           -- '상승 종목' 필터 (0보다 큰 경우)
    AND last_updated >= NOW() - INTERVAL 1 MINUTE  -- 실시간성 확인
ORDER BY 
    market_cap DESC;
