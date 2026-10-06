import request from '@/utils/request'

/** 分页查询宠物 */
export function getPetPageList(params) {
  return request({
    url: '/api/pet/list',
    method: 'get',
    params
  })
}

/** 新增宠物 */
export function createPetApi(data) {
  return request({
    url: '/api/pet',
    method: 'post',
    data
  })
}

/** 修改宠物 */
export function updatePetApi(petId, data) {
  return request({
    url: `/api/pet/${petId}`,
    method: 'put',
    data
  })
}

/** 删除宠物 */
export function deletePetApi(petId) {
  return request({
    url: `/api/pet/${petId}`,
    method: 'delete'
  })
}