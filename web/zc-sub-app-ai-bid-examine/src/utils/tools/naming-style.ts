/**
 * 将字符串（全小写的）转换为Pascal命名
 * @param str 字符串
 */
export const toPascalCase = (str: string) => {
  return str.substring(0, 1).toUpperCase() + str.substring(1);
};

/**
 * 将下划线命名的属性转换为驼峰命名
 * @param obj 响应对象
 */
export const snakeCaseToCamelCase = (obj: any) => {
  if (!obj || typeof obj !== 'object') {
    return;
  }

  if (obj instanceof Array) {
    obj.forEach((item) => {
      if (item && typeof item === 'object') {
        snakeCaseToCamelCase(item);
        return;
      }
    });
  } else {
    Object.keys(obj).forEach((key) => {
      if (obj[key] && typeof obj[key] === 'object') {
        snakeCaseToCamelCase(obj[key]);
      }
      const newKey = key.replace(/_(\w)/g, (all, letter) => letter.toUpperCase());
      if (newKey !== key) {
        obj[newKey] = obj[key];
        delete obj[key];
      }
    });
  }
};

/**
 * 将驼峰命名的属性转换为下划线命名
 * @param obj 请求对象
 */
export const camelCaseToSnakeCase = (obj: any) => {
  if (!obj || typeof obj !== 'object') {
    return;
  }

  Object.keys(obj).forEach((key) => {
    if (obj[key] && typeof obj[key] === 'object' && !(obj[key] instanceof Array)) {
      camelCaseToSnakeCase(obj[key]);
      return;
    }
    const newKey = key.replace(/([A-Z])/g, '_$1').toLowerCase();
    if (newKey !== key) {
      obj[newKey] = obj[key];
      delete obj[key];
    }
  });
};
