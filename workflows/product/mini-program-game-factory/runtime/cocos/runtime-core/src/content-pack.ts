export interface ContentPack {
  contentId: string;
  kernelId: 'circuit-untangle';
  locale: string;
  theme: string;
  copy: { title: string; win: string; lose: string };
  levelParameters: { gridSize: number; moves: number; targetCount: number };
  assets: Array<{ ref: string; license: string }>;
}

function record(value: unknown, name: string): Record<string, unknown> {
  if (!value || typeof value !== 'object' || Array.isArray(value)) {
    throw new Error(`${name} must be an object`);
  }
  return value as Record<string, unknown>;
}

function text(value: unknown, name: string): string {
  if (typeof value !== 'string' || !value.trim()) throw new Error(`${name} must be non-empty`);
  return value;
}

function integer(value: unknown, name: string): number {
  if (!Number.isInteger(value)) throw new Error(`${name} must be an integer`);
  return value as number;
}

export function normalizeContentPack(input: unknown): ContentPack {
  const raw = record(input, 'contentPack');
  const copy = record(raw.copy, 'copy');
  const level = record(raw.levelParameters ?? raw.level_parameters, 'levelParameters');
  if (!Array.isArray(raw.assets)) throw new Error('assets must be an array');
  return validateContentPack({
    contentId: text(raw.contentId ?? raw.content_id, 'contentId'),
    kernelId: text(raw.kernelId ?? raw.kernel_id, 'kernelId') as 'circuit-untangle',
    locale: text(raw.locale, 'locale'),
    theme: text(raw.theme, 'theme'),
    copy: {
      title: text(copy.title, 'copy.title'),
      win: text(copy.win, 'copy.win'),
      lose: text(copy.lose, 'copy.lose'),
    },
    levelParameters: {
      gridSize: integer(level.gridSize ?? level.grid_size, 'gridSize'),
      moves: integer(level.moves, 'moves'),
      targetCount: integer(level.targetCount ?? level.target_count, 'targetCount'),
    },
    assets: raw.assets.map((entry, index) => {
      const asset = record(entry, `assets[${index}]`);
      return { ref: text(asset.ref, `assets[${index}].ref`), license: text(asset.license, `assets[${index}].license`) };
    }),
  });
}

export function validateContentPack(input: ContentPack): ContentPack {
  if (input.kernelId !== 'circuit-untangle') throw new Error('kernelId must be circuit-untangle');
  const { gridSize, moves, targetCount } = input.levelParameters;
  if (gridSize < 3 || gridSize > 8) throw new Error('gridSize must be between 3 and 8');
  if (moves < 5 || moves > 80) throw new Error('moves must be between 5 and 80');
  if (targetCount < 1 || targetCount > 12) throw new Error('targetCount must be between 1 and 12');
  if (targetCount >= gridSize * gridSize) throw new Error('targetCount must leave one cell for the source');
  if (!input.assets.length) throw new Error('assets must contain rights metadata');
  for (const asset of input.assets) {
    if (!asset.ref || !asset.license) throw new Error('every asset requires ref and license');
  }
  return input;
}
