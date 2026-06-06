from flask import Flask, render_template, request, redirect, url_for
import configparser
import os
import subprocess
from streamget.logger import logger

app = Flask(__name__)

CONFIG_FILE = 'config/config.ini'
URL_CONFIG_FILE = 'config/URL_config.ini'


def read_config(file_path):
    config = configparser.ConfigParser(interpolation=None)
    try:
        with open(file_path, 'r', encoding='utf-8-sig') as f:
            content = f.read()
            if not content.strip().startswith('['):
                content = '[DEFAULT]\n' + content
                config.read_string(content)
            else:
                config.read(file_path, encoding='utf-8-sig')
    except FileNotFoundError:
        pass  # Return empty config if file not found
    return config


def write_config(config, file_path):
    with open(file_path, 'w', encoding='utf-8-sig') as configfile:
        config.write(configfile)


@app.route('/')
def index():
    return redirect(url_for('home_page'))


@app.route('/home', methods=['GET'])
def home_page():
    return render_template('index.html', active_tab='home')


recording_process = None

# 启动webui时自动启动main.py录制进程


def start_main_recording():
    global recording_process
    if recording_process is None or recording_process.poll() is not None:
        try:
            logger.info("WebUI启动时自动开始录制...")
            recording_process = subprocess.Popen(['python', 'main.py'],
                                                 cwd=os.getcwd())
        except Exception as e:
            logger.error(f"自动启动录制失败: {e}")


# 在Flask启动前自动调用
def run_with_auto_record():
    start_main_recording()
    app.run(host='0.0.0.0', port=5000)


@app.route('/url_config', methods=['GET', 'POST'])
def url_config_page():
    url_config_path = os.path.join(os.getcwd(), 'config', 'URL_config.ini')
    if request.method == 'POST':
        new_content = request.form['url_config_content']
        with open(url_config_path, 'w', encoding='utf-8-sig') as f:
            f.write(new_content)
        return redirect(url_for('url_config_page', success='true'))
    try:
        with open(url_config_path, 'r', encoding='utf-8-sig') as f:
            url_config_content = f.read()
    except FileNotFoundError:
        url_config_content = ''
    return render_template('index.html',
                           url_config_content=url_config_content,
                           active_tab='url_config')


@app.route('/recording_settings', methods=['GET', 'POST'])
def recording_settings_page():
    config_path = os.path.join(os.getcwd(), 'config', 'config.ini')
    if request.method == 'POST':
        config = read_config(config_path)
        for key, value in request.form.items():
            if '录制设置' in config and key in config['录制设置']:
                config.set('录制设置', key, value)
        write_config(config, config_path)
        return redirect(url_for('recording_settings_page', success='true'))
    config = read_config(config_path)
    return render_template('index.html',
                           config=config,
                           active_tab='recording_settings',
                           section='录制设置')


@app.route('/push_settings', methods=['GET', 'POST'])
def push_settings_page():
    config_path = os.path.join(os.getcwd(), 'config', 'config.ini')
    if request.method == 'POST':
        config = read_config(config_path)
        for key, value in request.form.items():
            if '推送配置' in config and key in config['推送配置']:
                config.set('推送配置', key, value)
        write_config(config, config_path)
        return redirect(url_for('push_settings_page', success='true'))
    config = read_config(config_path)
    return render_template('index.html',
                           config=config,
                           active_tab='push_settings',
                           section='推送配置')


@app.route('/cookie_settings', methods=['GET', 'POST'])
def cookie_settings_page():
    config_path = os.path.join(os.getcwd(), 'config', 'config.ini')
    if request.method == 'POST':
        config = read_config(config_path)
        for key, value in request.form.items():
            if 'Cookie' in config and key in config['Cookie']:
                config.set('Cookie', key, value)
        write_config(config, config_path)
        return redirect(url_for('cookie_settings_page', success='true'))
    config = read_config(config_path)
    return render_template('index.html',
                           config=config,
                           active_tab='cookie_settings',
                           section='Cookie')


@app.route('/account_settings', methods=['GET', 'POST'])
def account_settings_page():
    config_path = os.path.join(os.getcwd(), 'config', 'config.ini')
    if request.method == 'POST':
        config = read_config(config_path)
        for key, value in request.form.items():
            if '账号密码' in config and key in config['账号密码']:
                config.set('账号密码', key, value)
        write_config(config, config_path)
        return redirect(url_for('account_settings_page', success='true'))
    config = read_config(config_path)
    return render_template('index.html',
                           config=config,
                           active_tab='account_settings',
                           section='账号密码')


@app.route('/log')
def get_log():
    log_content = []
    log_file = os.path.join(os.getcwd(), 'logs', 'PlayURL.log')
    if os.path.exists(log_file):
        try:
            with open(log_file, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            # 从后往前找最新一组日志：遇到"共监测"开始收集，直到收集到足够信息
            mon = rec = detail = other = None
            for i in range(len(lines) - 1, -1, -1):
                s = lines[i].strip()
                if not s:
                    continue
                if 'xxxx' in s.lower():
                    continue
                if 'ERROR' in s or 'WebUI启动' in s:
                    continue
                if '序号' in s and detail is None:
                    detail = s
                elif '正在录制' in s and rec is None:
                    rec = s
                elif '没有正在录制' in s and other is None:
                    other = s
                elif '共监测' in s and mon is None:
                    mon = s
                    break  # 找到共监测就停止，这是该组的开头
            if mon:
                log_content.append(mon)
                if rec:
                    log_content.append(rec)
                if detail:
                    log_content.append(detail)
                if other:
                    log_content.append(other)
        except Exception as e:
            return f"Error reading log: {e}"
    if not log_content:
        return "暂无日志"
    return "\n".join(log_content)


if __name__ == '__main__':
    run_with_auto_record()