import requests, logging, os, yaml, time
from pathlib import Path
from dotenv import load_dotenv
import venv

load_dotenv(verbose=True)

log_dir = Path('logs')
if not log_dir.exists():
    log_dir.mkdir()
log_path = log_dir / '{}.log'.format(time.strftime('%Y%m%d-%H%M%S'))

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
fh = logging.FileHandler(filename=log_path, mode='w', encoding='UTF-8')
formatter = logging.Formatter('%(asctime)s - %(name)s:%(lineno)s - %(funcName)s - %(levelname)s - %(message)s')
fh.setFormatter(formatter)
logger.addHandler(fh)


class Config(object):
    def __init__(self, path):
        self.__path = Path(path)
        self.__text = ''
        self.dict = {}
        if self.__path.exists():
            self.read_text()

    def __repr__(self):
        return '<Config {}>'.format(self.__path)

    def load(self):
        self.dict = yaml.load(self.__text, Loader=yaml.FullLoader) or {}
        logger.info('{} loaded dict from text'.format(self))
        logger.debug('dict: {}'.format(self.dict))

    def dump(self):
        self.__text = yaml.dump(self.dict, allow_unicode=True, sort_keys=False)
        logger.info('{} dumped dict to text'.format(self))
        logger.debug('__text: {}'.format(self.__text))

    def read_text(self):
        self.__text = self.__path.read_text(encoding='UTF-8')
        logger.info('read yaml file {}'.format(self.__path))
        logger.debug('yaml text: {}'.format(self.__text))
        self.load()

    def download(self, url):
        response = requests.get(url)
        self.__text = response.text
        logger.info('downloaded {}'.format(url))
        logger.debug('downloaded content: {}'.format(self.__text))
        self.write_text(dump=False)  # 注意要直接把下载的text写进文件，不能把dict转成text
        self.load()

    def write_text(self, path=None, dump=True):
        if path:
            logger.info('{} __path changed to {}'.format(self, path))
            self.__path = Path(path)
        if dump:
            self.dump()
        self.__path.write_text(self.__text, encoding='UTF-8')
        logger.info('{} saved'.format(self.__path))
        logger.debug('text: {}'.format(self.__text))

    def uncomment(self):
        logger.debug('__text: {}'.format(self.__text))
        self.__text = self.__text.replace('#', '')
        logger.info('uncommented')
        logger.debug('__text: {}'.format(self.__text))
        self.load()

    def update(self, **kw):
        self.dict.update(**kw)
        logger.info('{} updated dict'.format(self))
        logger.debug('kw: {}'.format(kw))


if __name__ == '__main__':
    def process_jiyou(cfg: Config):
        groups = cfg.dict['Proxy Group']
        # 检查groups是否为list
        if not isinstance(groups, list):
            raise TypeError('Proxy Group should be list type')
        if groups:
            for group in groups:
                # 删除fallback组
                if group['type'] == 'fallback':
                    groups.pop(groups.index(group))
                elif group['type'] == 'select':
                    # select组改名为PROXY
                    group['name'] = 'PROXY'
                    # select组的proxies首个增加auto组
                    # TODO 插入的proxy名不写死，从groups中获取type=url-test的group的name
                    group['proxies'].insert(0, 'auto')


    base_cfg = Config(os.getenv('BASE_CONFIG_PATH', 'yaml/base.yaml'))
    rule_cfg = Config(os.getenv('RULE_CONFIG_PATH', 'yaml/rule.yaml'))
    proxy_cfg = Config(os.getenv('JIYOU_CONFIG_PATH', 'yaml/jiyou.yaml'))
    cfg = Config('yaml/config-{}.yaml'.format(time.strftime('%Y%m%d-%H%M%S')))

    proxy_cfg.download(os.getenv('CONFIG_URL'))
    proxy_cfg.uncomment()
    process_jiyou(proxy_cfg)

    cfg.update(**base_cfg.dict)
    cfg.update(**{
        'Proxy': proxy_cfg.dict['Proxy'],
        'Proxy Group': proxy_cfg.dict['Proxy Group']
    })
    cfg.update(Rule=rule_cfg.dict['Rule'])

    cfg.write_text()
    # 另存一份到clash的配置目录
    cfg.write_text(os.getenv('TARGET_PATH'))
    print('ok. wrote {}'.format(os.getenv('TARGET_PATH')))

    # TODO 配置文件同步到rspi
    # TODO rspi重载clash配置
