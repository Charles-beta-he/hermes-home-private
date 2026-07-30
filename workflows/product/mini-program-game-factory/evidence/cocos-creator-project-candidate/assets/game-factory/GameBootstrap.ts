import { _decorator, Component } from 'cc';
import { normalizeContentPack } from './core/content-pack.js';
import { applyAction, createGame, GameState, scoreState } from './core/gameplay-kernel.js';

const { ccclass, property } = _decorator;
const CONTENT_PACK = {
  "assets": [
    {
      "license": "original-required",
      "ref": "brief://rack-node"
    }
  ],
  "content_id": "data-center-repair-zh-cn",
  "copy": {
    "lose": "抢修超时",
    "title": "链路抢修",
    "win": "供电恢复"
  },
  "kernel_id": "circuit-untangle",
  "level_parameters": {
    "grid_size": 5,
    "moves": 28,
    "target_count": 4
  },
  "locale": "zh-CN",
  "theme": "数据中心抢修"
} as const;

@ccclass('GameBootstrap')
export class GameBootstrap extends Component {
  @property
  public seed = 20260727;

  private state: GameState | null = null;

  public onLoad(): void {
    this.state = createGame(normalizeContentPack(CONTENT_PACK), this.seed);
    this.node.emit('game-state-changed', this.snapshot());
  }

  public rotateNode(index: number): void {
    this.update({ type: 'rotate_node', index });
  }

  public swapAdjacent(first: number, second: number): void {
    this.update({ type: 'swap_adjacent', first, second });
  }

  public requestHint(): void {
    this.update({ type: 'request_hint' });
  }

  public snapshot(): Readonly<GameState> {
    if (!this.state) throw new Error('GameBootstrap has not loaded');
    return this.state;
  }

  public score(): number {
    return this.state ? scoreState(this.state) : 0;
  }

  private update(action: Parameters<typeof applyAction>[1]): void {
    if (!this.state) throw new Error('GameBootstrap has not loaded');
    this.state = applyAction(this.state, action);
    this.node.emit('game-state-changed', this.snapshot());
  }
}
