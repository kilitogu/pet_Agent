import request from '@/utils/request'

/** 分页查询宠物分类 */
export function getCategoryPageList(params) {
  return request({
    url: '/api/pet-category/list',
    method: 'get',
    params
  })
}

/** 新增宠物分类 */
export function createCategoryApi(data) {
  return request({
    url: '/api/pet-category',
    method: 'post',
    data
  })
}

/** 修改宠物分类 */
export function updateCategoryApi(categoryId, data) {
  return request({
    url: `/api/pet-category/${categoryId}`,
    method: 'put',
    data
  })
}

/** 删除宠物分类 */
export function deleteCategoryApi(categoryId) {
  return request({
    url: `/api/pet-category/${categoryId}`,
    method: 'delete'
  })
}