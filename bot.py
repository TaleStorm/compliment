from bot_config.bot_messages import dp, executor, on_startup, RedisMiddleware

if __name__ == '__main__':
    dp.middleware.setup(RedisMiddleware())
    executor.start_polling(dp, skip_updates=True, on_startup=on_startup)
