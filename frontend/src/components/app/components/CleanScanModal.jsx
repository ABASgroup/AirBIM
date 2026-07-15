import { useState } from "react";
import { Modal, FilledButton, UnfilledButton, Input } from "@ui";
import { cleanPointCloud } from "@/api/stage";

const AXIS = ["X", "Y", "Z"];

const defaultConfig = {
  deduplicate_cell_m: 0.001,
  poisson_sample_radius_m: "",
  statistical_outlier: true,
  outlier_mean_k: 16,
  outlier_multiplier: 2.5,
  radius_outlier_radius_m: "",
  radius_outlier_min_k: 4,
  z_mad_k: "",
  crop_min_xyz: ["", "", ""],
  crop_max_xyz: ["", "", ""],
  noise_class: 1,
  compress_output: "",
};

const toOptionalNumber = (value) => {
  if (value === "" || value === null || value === undefined) return null;
  const n = Number(value);
  return Number.isFinite(n) ? n : null;
};

const toOptionalTriple = (values) => {
  const triple = values.map(toOptionalNumber);
  if (triple.every((v) => v === null)) return null;
  return triple;
};

export const CleanScanModal = ({
  stageId,
  bounds,
  onClose,
  onSuccess,
}) => {
  const [config, setConfig] = useState(() => ({ ...defaultConfig }));
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState(null);

  const minXyz = bounds?.min_xyz ?? [0, 0, 0];
  const maxXyz = bounds?.max_xyz ?? [0, 0, 0];

  const updateField = (key, value) => {
    setConfig((prev) => ({ ...prev, [key]: value }));
  };

  const updateCrop = (kind, index, value) => {
    setConfig((prev) => {
      const next = [...prev[kind]];
      next[index] = value;
      return { ...prev, [kind]: next };
    });
  };

  const buildPayload = () => {
    const payload = {
      deduplicate_cell_m: toOptionalNumber(config.deduplicate_cell_m) ?? 0.001,
      poisson_sample_radius_m: toOptionalNumber(config.poisson_sample_radius_m),
      statistical_outlier: Boolean(config.statistical_outlier),
      outlier_mean_k: Number(config.outlier_mean_k) || 16,
      outlier_multiplier: Number(config.outlier_multiplier) || 2.5,
      radius_outlier_radius_m: toOptionalNumber(config.radius_outlier_radius_m),
      radius_outlier_min_k: Number(config.radius_outlier_min_k) || 4,
      z_mad_k: toOptionalNumber(config.z_mad_k),
      crop_min_xyz: toOptionalTriple(config.crop_min_xyz),
      crop_max_xyz: toOptionalTriple(config.crop_max_xyz),
      noise_class: Number(config.noise_class) || 1,
      compress_output:
        config.compress_output === ""
          ? null
          : config.compress_output === true || config.compress_output === "true",
    };
    return payload;
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError(null);
    setIsSubmitting(true);
    try {
      const payload = buildPayload();
      const res = await cleanPointCloud(stageId, payload);
      onSuccess?.(res.data);
      onClose?.();
    } catch (err) {
      const message =
        err?.response?.data?.message ||
        err?.message ||
        "Не удалось запустить очистку";
      setError(typeof message === "string" ? message : JSON.stringify(message));
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <form onSubmit={handleSubmit}>
      <Modal title="Параметры очистки скана" showBackdrop={true}>
        <p className="text-sm text-mute-text-color mb-3">
          Укажите параметры очистки. Пустые поля означают значения по умолчанию.
          Обрезка XYZ ограничена границами файла.
        </p>

        <div className="mb-4 p-3 rounded-[5px] bg-background-color text-sm">
          <div className="font-medium mb-2">Границы файла</div>
          <div className="grid grid-cols-3 gap-2">
            {AXIS.map((axis, i) => (
              <div key={axis}>
                <div className="text-mute-text-color">{axis}</div>
                <div>
                  min: {Number(minXyz[i]).toFixed(3)}
                </div>
                <div>
                  max: {Number(maxXyz[i]).toFixed(3)}
                </div>
              </div>
            ))}
          </div>
        </div>

        <div className="grid gap-3 max-h-[50vh] overflow-y-auto pr-1">
          <div>
            <label>Deduplicate cell (m)</label>
            <Input
              type="number"
              step="any"
              value={config.deduplicate_cell_m}
              onChange={(e) => updateField("deduplicate_cell_m", e.target.value)}
            />
          </div>
          <div>
            <label>Poisson sample radius (m)</label>
            <Input
              type="number"
              step="any"
              placeholder="не задано"
              value={config.poisson_sample_radius_m}
              onChange={(e) => updateField("poisson_sample_radius_m", e.target.value)}
            />
          </div>
          <div className="flex items-center gap-2">
            <input
              id="statistical_outlier"
              type="checkbox"
              checked={config.statistical_outlier}
              onChange={(e) => updateField("statistical_outlier", e.target.checked)}
            />
            <label htmlFor="statistical_outlier">Statistical outlier</label>
          </div>
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label>Outlier mean K</label>
              <Input
                type="number"
                value={config.outlier_mean_k}
                onChange={(e) => updateField("outlier_mean_k", e.target.value)}
              />
            </div>
            <div>
              <label>Outlier multiplier</label>
              <Input
                type="number"
                step="any"
                value={config.outlier_multiplier}
                onChange={(e) => updateField("outlier_multiplier", e.target.value)}
              />
            </div>
          </div>
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label>Radius outlier radius (m)</label>
              <Input
                type="number"
                step="any"
                placeholder="не задано"
                value={config.radius_outlier_radius_m}
                onChange={(e) => updateField("radius_outlier_radius_m", e.target.value)}
              />
            </div>
            <div>
              <label>Radius outlier min K</label>
              <Input
                type="number"
                value={config.radius_outlier_min_k}
                onChange={(e) => updateField("radius_outlier_min_k", e.target.value)}
              />
            </div>
          </div>
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label>Z MAD k</label>
              <Input
                type="number"
                step="any"
                placeholder="не задано"
                value={config.z_mad_k}
                onChange={(e) => updateField("z_mad_k", e.target.value)}
              />
            </div>
            <div>
              <label>Noise class</label>
              <Input
                type="number"
                value={config.noise_class}
                onChange={(e) => updateField("noise_class", e.target.value)}
              />
            </div>
          </div>

          <div>
            <label className="mb-1 block">Crop min XYZ</label>
            <div className="grid grid-cols-3 gap-2">
              {AXIS.map((axis, i) => (
                <Input
                  key={`min-${axis}`}
                  type="number"
                  step="any"
                  placeholder={`${axis} ≥ ${Number(minXyz[i]).toFixed(2)}`}
                  min={minXyz[i]}
                  max={maxXyz[i]}
                  value={config.crop_min_xyz[i]}
                  onChange={(e) => updateCrop("crop_min_xyz", i, e.target.value)}
                />
              ))}
            </div>
          </div>
          <div>
            <label className="mb-1 block">Crop max XYZ</label>
            <div className="grid grid-cols-3 gap-2">
              {AXIS.map((axis, i) => (
                <Input
                  key={`max-${axis}`}
                  type="number"
                  step="any"
                  placeholder={`${axis} ≤ ${Number(maxXyz[i]).toFixed(2)}`}
                  min={minXyz[i]}
                  max={maxXyz[i]}
                  value={config.crop_max_xyz[i]}
                  onChange={(e) => updateCrop("crop_max_xyz", i, e.target.value)}
                />
              ))}
            </div>
          </div>
        </div>

        {error && (
          <p className="text-sm text-red-500 mt-3">{error}</p>
        )}

        <div className="flex justify-end gap-3 mt-5">
          <UnfilledButton type="button" onClick={onClose} disabled={isSubmitting}>
            Отмена
          </UnfilledButton>
          <FilledButton type="submit" disabled={isSubmitting}>
            {isSubmitting ? "Запуск..." : "Применить и конвертировать"}
          </FilledButton>
        </div>
      </Modal>
    </form>
  );
};
