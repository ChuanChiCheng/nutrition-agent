"""Shared English response paths, including offline commands and recovery."""
import ast
import json
import re
from pathlib import Path
from types import SimpleNamespace
import pytest
from nutrition_demo.agent import DemoAgent, Settings, INSTRUCTIONS, HELP
from nutrition_demo.workflow import Workflow
from nutrition_demo.models import Result
from nutrition_demo.display import render
from nutrition_demo.tools import QUESTIONS


def english(value):
    assert not re.search(r'[\u3400-\u9fff]', str(value)), str(value)


def make_agent(service, steps=()):
    from test_demo_agent import Responses
    return DemoAgent(service, Workflow(service), SimpleNamespace(responses=Responses(steps)), Settings())


def test_default_instructions_help_and_owned_text_are_english():
    english(INSTRUCTIONS); english(HELP); english(json.dumps(QUESTIONS, ensure_ascii=False))
    assert 'English' in INSTRUCTIONS
    root=Path(__file__).resolve().parents[1]
    # Input recognition supports existing bilingual data; it is not response text.
    for name in ('agent.py','tools.py','workflow.py','catalog.py','display.py','__main__.py'):
        english((root/'nutrition_demo'/name).read_text())
    assert not (root/'nutrition_eval'/'english.py').exists()


def test_help_retry_unknown_commands_and_clarifications(stocked):
    agent=make_agent(stocked)
    for command in ('/help','/retry','/unknown','/preview','/confirm wrong','/reject wrong','/inventory-ok','/new-plan'):
        result=agent.handle(command)
        english(render(result))
    for topic in QUESTIONS:
        agent.workflow.save({**agent.workflow.load(),'clarifications':0})
        result=agent._dispatch('ask_user',{'topic':topic},'test-ask')
        assert result.ok
        english(render(result)); english(render(Result(True,agent._display([]))))
    agent.workflow.save({**agent.workflow.load(),'clarifications':3})
    assert not agent._dispatch('ask_user',{'topic':'batch'},'limit').ok


def test_display_all_control_states(stocked):
    agent=make_agent(stocked)
    original=agent.workflow.load()
    for extra in ({}, {'pending_preview':'preview-english'}, {'waiting_question':'Which batch?'},
                  {'proposal':{'id':'proposal-english','calculation':{'targets':{'passed':True}}}},
                  {'proposal':{'id':'proposal-english','calculation':{'targets':{'passed':False}}}}):
        agent.workflow.save({**original,**extra})
        for results in ([],[{'name':'query','result':{'ok':True,'data':{}}}]):
            english(render(Result(True,agent._display(results,limit=True))))


@pytest.mark.parametrize('recovery_command', ['/retry', None])
def test_english_recovery_after_model_error_and_explicit_retry(prepared, recovery_command):
    service,batch=prepared
    message='I ate one box from '+batch+' for lunch today.'
    args={'batch_id':batch,'eaten_on':'today','meal':'lunch','addon_override':None}
    agent=make_agent(service,[[('log_meal',args)],RuntimeError('interrupted')])
    result=agent.handle(message)
    assert not result.ok
    english(result.error)
    recovered=make_agent(service).handle(recovery_command or message)
    assert recovered.ok and recovered.data['recovered']
    english(recovered.data['message'])
    assert service.store.info()['counts']['events']==1


def test_error_and_rejection_rendering_are_english(stocked):
    agent=make_agent(stocked)
    for name,args in [('unknown',{}),('log_meal',{}),('preview_preparation',{})]:
        result=agent._dispatch(name,args,'invalid')
        assert not result.ok
        english(render(result))
    for result in (Result(False,{},'Invalid input'),Result(True,{}),
                   Result(True,{'rejected':'preview'}),
                   Result(True,{'tool_results':[{'result':{'ok':False,'error':'Invalid quantity'}}]})):
        english(render(result))


def test_cli_configuration_and_unexpected_errors_are_english(monkeypatch, capsys):
    from nutrition_demo import __main__ as cli
    monkeypatch.setattr('sys.argv', ['nutrition_demo'])
    monkeypatch.setenv('DATABASE_URL', '')
    assert cli.main() == 1
    english(capsys.readouterr().err)
    class BrokenStore:
        def __init__(self, *args):
            raise RuntimeError('must not expose this raw payload')
    monkeypatch.setattr(cli, 'Store', BrokenStore)
    assert cli.main() == 1
    error = capsys.readouterr().err
    english(error)
    assert 'RuntimeError' in error and 'raw payload' not in error
