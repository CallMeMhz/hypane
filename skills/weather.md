# 天气更新

## 任务

获取用户所在城市的天气信息并更新 Dashboard。

## 数据源

可选 API：
- OpenWeatherMap: https://api.openweathermap.org/data/2.5/weather
- 和风天气: https://devapi.qweather.com/v7/weather/now
- wttr.in (免费无需 key): https://wttr.in/Shanghai?format=j1

## 执行步骤

1. 读取 dashboard.json 获取用户城市设置
2. 调用天气 API 获取数据
3. 更新或创建 weather 卡片
4. 保存 dashboard.json

## 注意事项

- 这个任务通常由脚本执行，不需要 Agent
- 如果 API 需要 key，脚本中配置环境变量
