import importlib.util
import json
import re
from pathlib import Path
import sys
from playwright.sync_api import sync_playwright, expect
import argparse
parser=argparse.ArgumentParser(description='Optional Playwright browser workflow check')
parser.add_argument('--chromium',required=True)
parser.add_argument('--output-dir',required=True)
args=parser.parse_args()
root=Path(__file__).resolve().parents[2]
def load(name,path):
 s=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
ris=load('ris',root/'ris/scripts/ris.py');graph=load('graph',root/'project-plan/scripts/project_plan.py')
project=Path(args.output_dir).resolve();project.mkdir(parents=True,exist_ok=True)
ris.initialize(project,'Synthetic test')
record=ris.add_record(project,'plan','Synthetic decision map',(root/'project-plan/assets/research-plan-example.md').read_text())
plan=project/record['path'];config=project/'.ris/project.yaml'
ris.configure(project,ris.sha(config.read_bytes()),'milestones','autonomous',record['path'])
output='research/plans/map.html';graph.render(project,record['path'],output)
assert 'example-wildfire' in ris.context(project)['records'][-1]['text']
before=plan.read_bytes()
with sync_playwright() as p:
 browser=p.chromium.launch(executable_path=args.chromium,headless=True,args=['--no-sandbox'])
 page=browser.new_page(viewport={'width':1280,'height':900})
 errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
 page.goto((project/output).as_uri())
 branch=page.locator('details').first
 was_open=branch.evaluate('(el)=>el.open')
 branch.locator('summary').first.focus()
 page.keyboard.press('Enter')
 assert branch.evaluate('(el)=>el.open')!=was_open
 page.keyboard.press('Enter')
 assert branch.evaluate('(el)=>el.open')==was_open
 assert page.get_by_role('tab',name='구성요소별 선택지').get_attribute('aria-selected')=='true'
 assert page.locator('.card button').count()==0
 assert not page.locator('#candidateControls').is_visible()
 page.get_by_role('tab',name='후보 구성·비교').click()
 page.get_by_role('button',name='이 경로 가정하기').nth(1).click()
 assert 'fusion' in page.locator('#preview').inner_text() or '센서 결합' in page.locator('#preview').inner_text()
 assert '확정 기록은 바뀌지 않습니다' in page.locator('#warnings').inner_text()
 page.locator('#detail').get_by_role('button',name='→ D-002',exact=False).first.click()
 assert 'D-002' in page.locator('#detail h2').inner_text()
 page.get_by_role('button',name='← 이전 위치').click()
 assert 'D-001' in page.locator('#detail h2').inner_text()
 assert 'D-001' in page.locator('textarea').input_value()
 page.get_by_role('button',name='조사 요청 복사').click()
 expect(page.get_by_role('button',name=re.compile('^(복사됨|선택된 문구를 복사하세요)$'))).to_be_visible()
 page.get_by_role('button',name='상위로 이동: O-001').click()
 assert '성공 기준' in page.locator('#detail').inner_text()
 page.get_by_role('button',name='← 이전 위치').click()
 page.get_by_role('button',name='가상 선택 초기화').click()
 assert not page.locator('#preview').inner_text()
 page.screenshot(path=str(project/'desktop.png'),full_page=True)
 page.set_viewport_size({'width':390,'height':844})
 page.screenshot(path=str(project/'mobile.png'),full_page=True)
 assert page.evaluate('document.documentElement.scrollWidth <= window.innerWidth')
 assert not errors,errors
 expanded=ris.add_record(project,'plan','Expanded synthetic map',(root/'project-plan/assets/research-plan-expanded-example.md').read_text())
 graph.render(project,expanded['path'],'research/plans/expanded.html')
 page.set_viewport_size({'width':1280,'height':900})
 page.goto((project/'research/plans/expanded.html').as_uri())
 assert page.locator('.card').count()==5
 assert page.locator('#componentCatalog .component-entry').count()==13
 assert page.locator('.card button').count()==0
 assert not page.locator('#candidateComparison').is_visible()
 assert '결정 13개' in page.locator('#coverage').inner_text()
 assert page.locator('details').count()<50  # shared paths are references, not exponential trees
 for destination in ['D-040','D-041','D-060','D-070','D-080']:
  page.locator('#detail').get_by_role('button',name=re.compile('→ '+destination)).first.click()
  assert destination in page.locator('#detail h2').inner_text()
 page.get_by_role('button',name='상위로 이동: D-070').click()
 assert 'D-070' in page.locator('#detail h2').inner_text()
 page.screenshot(path=str(project/'expanded-desktop.png'),full_page=True)
 page.set_viewport_size({'width':390,'height':844})
 page.screenshot(path=str(project/'expanded-mobile.png'),full_page=True)
 assert page.evaluate('document.documentElement.scrollWidth <= window.innerWidth')
 assert not errors,errors
 fixture,_=graph.load(root/'project-plan','assets/research-plan-example.md')
 fixture['plan_id']='candidate-reuse-fixture'
 fixture['nodes'][2]['selection_mode']='multiple'
 fixture['candidates']=[{'id':'A','title':'후보 A','selections':{'D-001':['rgb'],'D-002':['public']}},{'id':'B','title':'후보 B','selections':{'D-001':['rgb'],'D-002':['flight']}}]
 fixture['current_candidate']='A'
 fixture['incompatible']=[[['D-001','fusion'],['D-002','public']]]
 candidate_record=ris.add_record(project,'plan','Candidate reuse test','```project-plan\n'+json.dumps(fixture,ensure_ascii=False)+'\n```\n')
 candidate_source=project/candidate_record['path'];candidate_before=candidate_source.read_bytes()
 graph.render(project,candidate_record['path'],'research/plans/candidates.html')
 page.set_viewport_size({'width':1280,'height':900});page.goto((project/'research/plans/candidates.html').as_uri())
 page.get_by_role('tab',name='후보 구성·비교').click()
 def card(title):return page.locator('.card').filter(has=page.get_by_role('heading',name=title,exact=True))
 def pressed(title):return card(title).get_by_role('button').get_attribute('aria-pressed')=='true'
 assert pressed('일반 카메라')
 assert page.locator('#candidateComparison').get_by_role('cell',name='일반 카메라',exact=True).count()==2
 page.get_by_label('후보 선택').select_option('B')
 assert pressed('일반 카메라')
 page.locator('#detail').get_by_role('button',name=re.compile('→ D-002')).first.click()
 assert pressed('비행 수집') and not pressed('공개 데이터')
 card('공개 데이터').get_by_role('button').click()
 assert pressed('비행 수집') and pressed('공개 데이터')
 page.get_by_label('후보 선택').select_option('A')
 assert pressed('공개 데이터') and not pressed('비행 수집')
 page.get_by_role('button',name='상위로 이동: D-001').click()
 card('센서 결합').get_by_role('button').click()
 assert '함께 선택할 수 없는 조합' in page.locator('#warnings').inner_text()
 page.get_by_label('후보 선택').select_option('B')
 assert pressed('일반 카메라') and not pressed('센서 결합')
 assert '함께 선택할 수 없는 조합' not in page.locator('#warnings').inner_text()
 page.get_by_role('button',name='가상 선택 초기화').click()
 assert '공개 데이터 + 비행 수집' not in page.locator('#candidateComparison').inner_text()
 page.get_by_label('후보 선택').select_option('A');assert pressed('센서 결합')
 page.get_by_label('후보 선택').select_option('B')
 page.get_by_role('button',name='현재 후보 복제').click()
 assert pressed('일반 카메라')
 card('센서 결합').get_by_role('button').click()
 assert pressed('센서 결합')
 page.get_by_label('후보 선택').select_option('B');assert pressed('일반 카메라')
 page.get_by_label('후보 선택').select_option('candidate-3');assert pressed('센서 결합')
 page.get_by_role('button',name='가상 선택 초기화').click();assert pressed('일반 카메라')
 page.get_by_role('button',name='빈 후보 추가').click()
 assert page.locator('.card button[aria-pressed=true]').count()==0
 page.get_by_label('후보 선택').select_option('A');assert pressed('센서 결합')
 assert '"selections"' in page.locator('textarea').input_value()

 page.get_by_role('tab',name='구성요소별 선택지').click()
 assert page.locator('#componentsPanel').is_visible() and not page.locator('#candidatesPanel').is_visible()
 page.locator('#componentCatalog').get_by_role('button',name='어떻게 검증할까?',exact=True).click()
 assert page.locator('.card button').count()==0
 assert not page.locator('#candidateControls').is_visible()
 page.screenshot(path=str(project/'components-desktop.png'),full_page=True)
 page.set_viewport_size({'width':390,'height':844})
 page.screenshot(path=str(project/'components-mobile.png'),full_page=True)
 assert page.evaluate('document.documentElement.scrollWidth <= window.innerWidth')
 page.set_viewport_size({'width':1280,'height':900})
 page.get_by_role('button',name='이 구성요소로 후보 구성').click()
 assert page.get_by_label('후보 선택').input_value()=='A'
 assert pressed('공개 데이터') and not pressed('비행 수집')
 row=page.locator('#candidateComparison').get_by_role('row').filter(has=page.get_by_role('rowheader',name='관측 수단을 선택할까?',exact=True))
 row.locator('td').nth(1).get_by_role('button').click()
 assert page.get_by_label('후보 선택').input_value()=='B'
 assert 'D-001' in page.locator('#detail h2').inner_text() and pressed('일반 카메라')
 page.get_by_label('후보 선택').select_option('A');assert pressed('센서 결합')
 page.get_by_role('tab',name='후보 구성·비교').focus();page.keyboard.press('ArrowLeft')
 assert page.locator('#componentsPanel').is_visible()
 page.keyboard.press('ArrowRight');assert page.locator('#candidatesPanel').is_visible()
 assert candidate_source.read_bytes()==candidate_before
 page.screenshot(path=str(project/'candidates-desktop.png'),full_page=True)
 page.set_viewport_size({'width':390,'height':844});page.screenshot(path=str(project/'candidates-mobile.png'),full_page=True)
 assert page.evaluate('document.documentElement.scrollWidth <= window.innerWidth')
 assert not errors,errors
 browser.close()
assert plan.read_bytes()==before
print(json.dumps({'browser':'PASS','resume':'PASS','source_unchanged':True,'plan':str(plan),'html':str(project/output)},ensure_ascii=False))
