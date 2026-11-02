from typing import Annotated, List, Optional
from fastapi import APIRouter, BackgroundTasks, Depends, File, Form, UploadFile, status
from app.products.dto.CreateProduct import CreateProduct
from app.products.dto.UpdateProduct import UpdateProduct
from app.products.dto.ProductResponse import ProductResponse
from app.products.service import ProductService
from app.auth.dto.MessageResponse import MessageResponse
from app.auth.dependecies import require_permissions

router = APIRouter(prefix="/product", tags=['product'])

@router.post("", response_model=ProductResponse, status_code=status.HTTP_201_CREATED)
def create_product(background_tasks: BackgroundTasks, data: Annotated[CreateProduct, Form()], files: List[UploadFile] = File(default=[]), service: ProductService = Depends(), current_user = Depends(require_permissions("product.create"))):
    return service.create_product(data, files, current_user, background_tasks)

@router.get("", response_model=List[ProductResponse])
def list_products(search: Optional[str] = None, model_number: Optional[str] = None, service: ProductService = Depends(), current_user = Depends(require_permissions("product.view"))):
    return service.list_products(search, model_number)

@router.get("/{product_id}", response_model=ProductResponse)
def get_product(product_id: int, service: ProductService = Depends(), current_user = Depends(require_permissions("product.view"))):
    return service.get_product_with_documents(product_id)

@router.patch("/{product_id}", response_model=ProductResponse)
def update_product(product_id: int, background_tasks: BackgroundTasks, data: Annotated[UpdateProduct, Form()], files: List[UploadFile] = File(default=[]), service: ProductService = Depends(), current_user = Depends(require_permissions("product.update"))):
    return service.update_product(product_id, data, files, current_user, background_tasks)

@router.delete("/{product_id}", response_model=MessageResponse)
def delete_product(product_id: int, service: ProductService = Depends(), current_user = Depends(require_permissions("product.delete"))):
    return service.delete_product(product_id)
