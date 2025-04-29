from pocketflow import Flow

from .nodes import DecideAction, SearchWeb, AnswerEditor, SupervisorNode, EvaluateImage


def create_agent_inner_flow():
    """
    创建并连接节点以形成完整的代理流程。
    
    流程如下：
    1. DecideAction 节点决定是搜索还是回答
    2. 如果选择搜索，转到 SearchWeb 节点
    3. 如果选择回答，转到 AnswerQuestion 节点
    4. SearchWeb 完成后，返回 DecideAction
    
    返回:
        Flow: 一个完整的研究代理流程
    """
    # 创建每个节点的实例
    decide = DecideAction()
    search = SearchWeb()
    answer = AnswerEditor()

    # 连接节点
    # 如果 DecideAction 返回 "search"，转到 SearchWeb
    decide - "search" >> search

    # 如果 DecideAction 返回 "answer"，转到 AnswerQuestion
    decide - "answer" >> answer

    # SearchWeb 完成后返回 "decide"，回到 DecideAction
    search - "decide" >> decide

    # 创建并返回流程，从 DecideAction 节点开始
    return Flow(start=decide)


def create_agent_flow():
    """
    创建一个带有监督的代理流程，将整个代理流程视为一个节点，并将监督节点放在其外部。

    流程如下：
    1. 内部代理流程进行研究并生成回答
    2. SupervisorNode 检查回答是否有效
    3. 如果回答有效，流程完成
    4. 如果回答无效，重新启动内部代理流程

    返回:
        Flow: 一个带有监督的完整研究代理流程
    """
    # 创建内部流程
    agent_flow = create_agent_inner_flow()

    # 创建监督节点
    supervisor = SupervisorNode()
    # apply_style = ApplyStyle()
    eval_image = EvaluateImage()

    # 连接组件
    # 在 agent_flow 完成后，转到 supervisor
    agent_flow >> supervisor
    # 如果 supervisor 批准回答，转到 apply_style
    supervisor - "approved" >> eval_image

    # apply_style - "final-article" >> eval_image
    # 如果 supervisor 拒绝回答，则返回到 agent_flow
    supervisor - "retry" >> agent_flow

    # 创建并返回外部流程，从 agent_flow 开始
    return Flow(start=agent_flow)
