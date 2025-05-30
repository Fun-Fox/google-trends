from pocketflow import Flow

from agent.nodes import ContentParaphraser, WriteSupervisorNode

__all__ = ["content_flow"]
def content_flow():
    """
    创建一个带有监督的代理流程，将整个代理流程视为一个节点，并将监督节点放在其外部。

    返回:
        Flow: 一个带有监督的完整研究代理流程
    """

    write_in_style= ContentParaphraser()
    # 创建监督节点
    supervisor = WriteSupervisorNode()

    # 连接组件
    write_in_style - "final_article" >> supervisor


    # supervisor - "retry" >> write_in_style

    # 创建并返回外部流程，从 agent_flow 开始
    return Flow(start=write_in_style)
