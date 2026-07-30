declare module 'cc' {
  export interface CocosDecoratorApi {
    ccclass(name: string): ClassDecorator;
    property(target: object, propertyKey: string | symbol): void;
  }
  export const _decorator: CocosDecoratorApi;
  export class Node {
    emit(event: string, ...args: unknown[]): void;
  }
  export class Component {
    readonly node: Node;
  }
}
